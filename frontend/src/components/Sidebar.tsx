// src/components/Sidebar.tsx
import React from 'react';
import {
    LayoutDashboard,
    Library,
    History,
    BookMarked,
    BarChart3,
    LogOut,
    User as UserIcon,
    FileText,
    PenTool,
    Mic,
    BookOpenCheck
} from 'lucide-react';
import type { ViewType, User } from '../types';

interface SidebarProps {
    currentView: ViewType;
    setCurrentView: (view: ViewType) => void;
    user: User | null;
    onLogout: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, setCurrentView, user, onLogout }) => {
    const menuItems = [
        { id: 'discover', label: 'Discover', icon: <LayoutDashboard size={20} /> },
        { id: 'library', label: 'Library', icon: <Library size={20} /> },
        { id: 'history', label: 'History', icon: <History size={20} /> },
        { id: 'vocabulary', label: 'Vocabulary', icon: <BookMarked size={20} /> },
        { id: 'stats', label: 'Stats', icon: <BarChart3 size={20} /> },
    ];

    const practiceItems = [
        { id: 'test', label: 'Reading Test', icon: <FileText size={20} /> },
        { id: 'vocabulary_test', label: 'Vocabulary Test', icon: <BookOpenCheck size={20} /> },
        { id: 'writing', label: 'Writing Coach', icon: <PenTool size={20} /> },
        { id: 'speaking', label: 'Speaking Coach', icon: <Mic size={20} /> },
    ];

    return (
        <div className="w-64 bg-white dark:bg-slate-900 h-screen border-r border-slate-200 dark:border-slate-800 flex flex-col fixed left-0 top-0 z-20 overflow-y-auto">
            <div className="p-6">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                    Faga
                </h1>
                <p className="text-xs text-slate-500 font-medium">Adaptive English Reader</p>
            </div>

            <nav className="flex-1 px-4 space-y-6">
                <div className="space-y-1">
                    <div className="text-xs font-bold text-slate-400 uppercase px-3 mb-2">Learn</div>
                    {menuItems.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setCurrentView(item.id as ViewType)}
                            className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${currentView === item.id
                                ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 font-semibold shadow-sm'
                                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                                }`}
                        >
                            {item.icon}
                            <span>{item.label}</span>
                        </button>
                    ))}
                </div>

                <div className="space-y-1">
                    <div className="text-xs font-bold text-slate-400 uppercase px-3 mb-2">Practice</div>
                    {practiceItems.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setCurrentView(item.id as ViewType)}
                            className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${currentView === item.id
                                ? 'bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400 font-semibold shadow-sm'
                                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                                }`}
                        >
                            {item.icon}
                            <span>{item.label}</span>
                        </button>
                    ))}
                </div>
            </nav>

            <div className="p-4 border-t border-slate-200 dark:border-slate-800">
                {user ? (
                    <div className="space-y-4">
                        <div className="flex items-center space-x-3 px-2">
                            <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center text-blue-600 dark:text-blue-400">
                                <UserIcon size={20} />
                            </div>
                            <div className="overflow-hidden">
                                <p className="text-sm font-semibold truncate">{user.username}</p>
                                <p className="text-xs text-slate-500 uppercase">{user.english_level}</p>
                            </div>
                        </div>
                        <button
                            onClick={onLogout}
                            className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-red-50 hover:text-red-600 dark:text-slate-400 dark:hover:bg-red-900/10 transition-colors"
                        >
                            <LogOut size={18} />
                            <span className="text-sm font-medium">Logout</span>
                        </button>
                    </div>
                ) : (
                    <p className="text-xs text-center text-slate-500 italic">Not logged in</p>
                )}
            </div>
        </div>
    );
};

export default Sidebar;
