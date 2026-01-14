# 需要安装 deep-translator
# pip install deep-translator

import random
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from deep_translator import GoogleTranslator
from models import VocabularyItem, StandardVocabulary, User

class VocabularyService:
    def __init__(self, db_session: Session):
        self.db = db_session

    # --- 1. Import CSV Data (Setup) ---
    def import_csv_data(self, list_name: str, file_path: str):
        """
        Reads your CSV (e.g., TOEFL.csv) and saves words to the database.
        """
        import csv
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                new_objects = []
                for row in reader:
                    if row:
                        # Format: "word" OR "word, definition"
                        word_text = row[0].strip()
                        def_text = row[1].strip() if len(row) > 1 else None
                        
                        if word_text:
                            new_objects.append(StandardVocabulary(
                                list_name=list_name, 
                                word=word_text,
                                definition=def_text
                            ))
                self.db.bulk_save_objects(new_objects)
                self.db.commit()
                print(f"✅ Imported words for {list_name}")
        except Exception as e:
            print(f"❌ Error importing CSV: {e}")

    # --- 2. Daily Learning (The "API" & "Graph" Part) ---
    def get_daily_learning(self, user_id: int):
        """
        Draws random words based on user speed.
        Enriches them with: Translation, Definition, Example, and Graph Data.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user: return []

        # 1. Find words user ALREADY has (to avoid duplicates)
        existing_words = self.db.query(VocabularyItem.word).filter(VocabularyItem.user_id == user_id)
        
        # 2. Draw NEW random words based on User Preference (Speed)
        candidates = self.db.query(StandardVocabulary).filter(
            StandardVocabulary.list_name == user.current_vocab_list,
            ~StandardVocabulary.word.in_(existing_words)
        ).order_by(func.random()).limit(user.words_per_day).all()

        results = []
        for cand in candidates:
            # 3. Fetch API Data (Definition + Synonyms/Graph)
            api_data = self._fetch_api_data(cand.word)
            
            # 4. Fetch Translation (English -> Chinese)
            try:
                translation = GoogleTranslator(source='auto', target='zh-CN').translate(cand.word)
            except:
                translation = "Translation unavailable"

            # Use CSV definition as backup if API fails
            final_def = api_data['definition']
            if final_def == "No definition found." and cand.definition:
                final_def = cand.definition

            # 5. Save to User's Vocabulary List
            new_item = VocabularyItem(
                user_id=user.id,
                word=cand.word,
                definition=final_def,
                translation=translation, 
                example_sentence=api_data['example'],
                synonyms=api_data['synonyms_graph'], # <--- The Graph Data
                image_url=f"https://loremflickr.com/400/300/{cand.word}"
            )
            self.db.add(new_item)
            
            results.append({
                "word": cand.word,
                "translation": translation,
                "definition": final_def,
                "example": api_data['example'],
                "synonyms_graph": api_data['synonyms_graph'],
                "image_url": new_item.image_url
            })
        
        self.db.commit()
        return results

    def _fetch_api_data(self, word):
        """
        Helper: Calls Dictionary API for Definition and Synonyms (Graph).
        """
        data = {
            "definition": "No definition found.", 
            "example": "", 
            "synonyms_graph": {"nodes": [], "links": []}
        }
        
        try:
            resp = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
            if resp.status_code == 200:
                json_data = resp.json()[0]
                
                # Get Definition & Example
                if 'meanings' in json_data:
                    meaning = json_data['meanings'][0]
                    # Prefer Noun/Verb
                    for m in json_data['meanings']:
                        if m.get('partOfSpeech') in ['noun', 'verb']:
                            meaning = m
                            break

                    def_obj = meaning['definitions'][0]
                    data['definition'] = def_obj.get('definition', '')
                    data['example'] = def_obj.get('example', '')
                    
                    # --- BUILD GRAPH DATA ---
                    syns = meaning.get('synonyms', [])[:5] 
                    nodes = [{"id": word, "group": 1}] # Center Node
                    links = []
                    for s in syns:
                        nodes.append({"id": s, "group": 2}) # Synonym Nodes
                        links.append({"source": word, "target": s})
                    
                    data['synonyms_graph'] = {"nodes": nodes, "links": links}
        except Exception:
            pass
            
        return data

    # --- 3. Vocabulary Book & Quiz Logic ---

    def get_vocabulary_book(self, user_id: int, filter_type='mistakes'):
        """
        Returns the user's word list. 
        If filter_type='mistakes', only returns words they got wrong.
        """
        query = self.db.query(VocabularyItem).filter(VocabularyItem.user_id == user_id)
        if filter_type == 'mistakes':
            query = query.filter(VocabularyItem.mistake_count > 0)
        return query.order_by(VocabularyItem.next_review_at).all()

    def submit_quiz_result(self, user_id: int, word: str, is_correct: bool):
        """
        Updates the word status. 
        If WRONG -> Adds to 'Mistakes', Resets Progress (Sent to Vocabulary Book).
        """
        item = self.db.query(VocabularyItem).filter(
            VocabularyItem.user_id == user_id, 
            VocabularyItem.word == word
        ).first()
        
        if not item: return

        item.last_reviewed = datetime.utcnow()
        
        if is_correct:
            # Spaced Repetition: Delay next review
            item.consecutive_correct += 1
            days_delay = 2 ** item.consecutive_correct 
            item.next_review_at = datetime.utcnow() + timedelta(days=days_delay)
            if item.consecutive_correct >= 5:
                item.is_mastered = 1
        else:
            # WRONG: Sent to Vocabulary Book (Reset Progress)
            item.consecutive_correct = 0
            item.mistake_count += 1
            item.is_mastered = 0
            item.next_review_at = datetime.utcnow() # Review Immediately

        self.db.commit()

    def generate_smart_quiz(self, user_id: int):
        """
        Generates a test based on user's 'words_per_day' preference.
        """
        # 1. Determine Quiz Size based on User Preference
        user = self.db.query(User).filter(User.id == user_id).first()
        quiz_size = user.words_per_day if user else 10

        # 2. Priority 1: Words due for review or Mistakes
        review_candidates = self.db.query(VocabularyItem).filter(
            VocabularyItem.user_id == user_id,
            VocabularyItem.next_review_at <= datetime.utcnow(),
            VocabularyItem.is_mastered == 0
        ).limit(quiz_size).all()
        
        # 3. Priority 2: Fill with random learned words
        if len(review_candidates) < quiz_size:
            existing_ids = [r.id for r in review_candidates]
            needed = quiz_size - len(review_candidates)
            
            fillers = self.db.query(VocabularyItem).filter(
                VocabularyItem.user_id == user_id,
                ~VocabularyItem.id.in_(existing_ids)
            ).order_by(func.random()).limit(needed).all()
            
            review_candidates.extend(fillers)

        # 4. Generate Questions
        quiz_data = []
        for target in review_candidates:
            # Get Distractors from Standard List
            distractors = self.db.query(StandardVocabulary).filter(
                StandardVocabulary.word != target.word
            ).order_by(func.random()).limit(3).all()
            
            options = [target.definition]
            for d in distractors:
                # Use standard definition or fallback
                def_text = d.definition if d.definition else f"Definition of {d.word}"
                options.append(def_text)

            random.shuffle(options)
            
            quiz_data.append({
                "word": target.word,
                "question": f"What is the definition of '{target.word}'?",
                "options": options,
                "correct_answer": target.definition,
                "is_review": target.mistake_count > 0 
            })
            
        return quiz_data