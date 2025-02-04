import React, { useEffect, useState } from "react";
import { deleteChat, renameChat } from "../api/chatAPI";
import { FaTrash, FaEdit } from "react-icons/fa";
import { BsThreeDots } from "react-icons/bs";
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
  }


  return (
    <div className="w-1/4 h-screen bg-gray-900 text-gray-300 flex flex-col">
      <div className="p-4 border-b border-gray-700">
      <Button onClick={onNewChat} className="w-full h-16 bg-gray-800 hover:bg-gray-700 text-white flex items-center justify-center space-x-3">
        <FaEdit size={32} className="text-gray-300" />
        <span className="text-xl" >New Chat</span>
      </Button>

      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        <ul>
        {sidebarChats.map((chat) => (
            <li
              key={chat.chat_id}
              className={`cursor-pointer hover:bg-gray-700 p-2 rounded text-lg flex justify-between items-center border-b border-gray-700 ${
                currentChatId === chat.chat_id ? "bg-gray-600" : ""
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
                  className="flex-1 bg-gray-800 text-gray-300 rounded p-1"
                  placeholder="Enter new title"
                  autoFocus
                />
              ) : (
                <span>{chat.title || "Untitled Chat"}</span>
              )}

              <DropdownMenu >
                <DropdownMenuTrigger>
                <Button variant="ghost" className="hover:bg-gray-600"><BsThreeDots /></Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="bg-gray-800 border border-gray-800 shadow-[0px_2px_4px_rgba(255,255,255,0.3)]">
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingChatId(chat.chat_id);
                      setNewTitle(chat.title || "");
                    }}
                    className="flex items-center hover:bg-gray-700"
                  >
                    <DropdownMenuShortcut><FaEdit size={18} className="text-gray-300" /></DropdownMenuShortcut>
                    <p className="text-gray-300" >Rename Chat</p>
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteChat(chat.chat_id);
                    }}
                    className="flex items-center hover:bg-gray-700"
                  >
                    <DropdownMenuShortcut><FaTrash size={18} className="text-gray-300" /></DropdownMenuShortcut>
                    <p className="text-gray-300">Delete Chat</p>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default ChatSidebar;
