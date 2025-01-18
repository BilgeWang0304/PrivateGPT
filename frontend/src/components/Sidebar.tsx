import React, { useEffect, useState } from "react";

interface Chat {
  chat_id: string;
  title: string;
}

interface SidebarProps {
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
  chats: Chat[];
}

const Sidebar: React.FC<SidebarProps> = ({ onSelectChat, onNewChat }) => {
  const [chats, setChats] = useState<Chat[]>([]);

  useEffect(() => {
    fetchChats();
  }, []);

  const fetchChats = async () => {
    const response = await fetch("http://127.0.0.1:8000/chats");
    const data = await response.json();
    setChats(data);
  };

  return (
    <div className="w-1/4 h-screen bg-gray-900 text-gray-300 flex flex-col">
      <div className="p-4 border-b border-gray-700">
        <button
          onClick={onNewChat}
          className="w-full py-2 px-4 bg-gray-800 hover:bg-gray-700 text-white rounded-md"
        >
          + New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {chats.map((chat) => (
          <div
            key={chat.chat_id}
            onClick={() => onSelectChat(chat.chat_id)}
            className="bg-gray-800 p-3 rounded-md hover:bg-gray-700 cursor-pointer"
          >
            <p className="text-sm">{chat.title}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Sidebar;
