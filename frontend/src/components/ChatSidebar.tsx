import React, { useEffect, useState } from "react";
import { deleteChat, renameChat } from "../api/chatAPI";
import { FaTrash, FaEdit, FaComments, FaSun, FaMoon } from "react-icons/fa";
import { BsThreeDots } from "react-icons/bs";
import { useTheme } from "./themeContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuShortcut
} from "./ui/dropdown-menu";
import { Button } from "./ui/button"

interface Chat {
  chat_id: string;
  title: string;
}

interface SidebarProps {
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
  chats: Chat[];
  onChatDeleted: (chatId: string) => void;
  currentChatId: string | null;
}

const ChatSidebar: React.FC<SidebarProps> = ({ onSelectChat, onNewChat, chats, onChatDeleted, currentChatId }) => {
  const { isDarkMode, toggleTheme } = useTheme();
  const [sidebarChats, setSidebarChats] = useState<Chat[]>(chats);
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState<string>("");

  useEffect(() => {
    setSidebarChats(chats);
  }, [chats]);

  const handleDeleteChat = async (chatId: string) => {
    try {
      await deleteChat(chatId);
      onChatDeleted(chatId); 
    } catch (error) {
      console.error("Error deleting chat:", error);
    }
  };

  const handleRenameChat = async (chatId: string) => {
    if (!newTitle.trim()) return;

    try {
      await renameChat(chatId, newTitle);
      setSidebarChats((prev) =>
        prev.map((chat) => (chat.chat_id === chatId ? { ...chat, title: newTitle } : chat))
      );
      setEditingChatId(null);
      setNewTitle("");
    } catch (error) {
      console.error("Error renaming chat:", error);
    }
  };

  return (
    <div className={`w-1/4 h-screen ${isDarkMode ? "bg-gray-900 text-gray-300" : "bg-gray-100 text-gray-800"} flex flex-col`}>
      {/* New Chat Button */}
      <div className={`p-4 border-b ${isDarkMode ? "border-gray-700" : "border-gray-300"}`}>
        <Button 
          onClick={onNewChat} 
          className={`w-full h-16 py-6 ${isDarkMode ? "bg-gray-800 hover:bg-gray-700 text-white" : "bg-gray-200 hover:bg-gray-300 text-gray-800"} flex items-center justify-center space-x-3`}
        >
          <div className="text-4xl">
            <FaEdit />
          </div>
          <span className="text-2xl">New Chat</span>
        </Button>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        <h2 className={`text-xl font-bold mb-4 pt-2 flex items-center gap-2 ${isDarkMode ? "text-gray-300" : "text-gray-800"}`}>
          <FaComments className="text-lg" />
          <span>All Chats</span>
        </h2>
        <ul>
          {sidebarChats.map((chat) => (
            <li
              key={chat.chat_id}
              className={`cursor-pointer p-2 rounded text-lg flex justify-between items-center border-b ${isDarkMode ? "hover:bg-gray-700 border-gray-700" : "hover:bg-gray-300 border-gray-300"} ${
                currentChatId === chat.chat_id ? (isDarkMode ? "bg-gray-600" : "bg-gray-300") : ""
              }`}
              onClick={() => onSelectChat(chat.chat_id)}
            >
              {editingChatId === chat.chat_id ? (
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleRenameChat(chat.chat_id);
                    if (e.key === "Escape") setEditingChatId(null);
                  }}
                  className={`flex-1 rounded p-1 ${isDarkMode ? "bg-gray-800 text-gray-300" : "bg-gray-200 text-gray-800"}`}
                  placeholder="Enter new title"
                  autoFocus
                />
              ) : (
                <span>{chat.title || "Untitled Chat"}</span>
              )}

              <DropdownMenu>
                <DropdownMenuTrigger>
                  <Button variant="ghost" className={isDarkMode ? "hover:bg-gray-600" : "hover:bg-gray-300"}>
                    <BsThreeDots />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className={`border ${isDarkMode ? "bg-gray-800 border-gray-800 shadow-[0px_2px_4px_rgba(255,255,255,0.3)]" : "bg-gray-200 border-gray-300 shadow-[0px_2px_4px_rgba(0,0,0,0.3)]"}`}>
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingChatId(chat.chat_id);
                      setNewTitle(chat.title || "");
                    }}
                    className={`flex items-center ${isDarkMode ? "hover:bg-gray-700" : "hover:bg-gray-300"}`}
                  >
                    <DropdownMenuShortcut><FaEdit size={20} className={isDarkMode ? "text-gray-300" : "text-gray-800"} /></DropdownMenuShortcut>
                    <p className={isDarkMode ? "text-gray-300" : "text-gray-800"}>Rename Chat</p>
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteChat(chat.chat_id);
                    }}
                    className={`flex items-center ${isDarkMode ? "hover:bg-gray-700" : "hover:bg-gray-300"}`}
                  >
                    <DropdownMenuShortcut><FaTrash size={20} className="text-red-500" /></DropdownMenuShortcut>
                    <p className="text-red-500">Delete Chat</p>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </li>
          ))}
        </ul>
      </div>

      {/* Theme Toggle Buttons at the Bottom */}
      <div className={`p-4 border-t flex justify-center ${isDarkMode ? "border-gray-700" : "border-gray-300"}`}>
        <button
          onClick={toggleTheme}
          className="p-2 rounded-full transition-colors"
        >
          {isDarkMode ? (
            <FaSun size={24} className="text-yellow-400 hover:text-yellow-500" />
          ) : (
            <FaMoon size={24} className="text-gray-600 hover:text-gray-700" />
          )}
        </button>
      </div>
    </div>
  );
};

export default ChatSidebar;
