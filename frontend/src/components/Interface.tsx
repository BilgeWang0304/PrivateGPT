import React, { useEffect, useState } from "react";
import Sidebar from "./Sidebar";
import MessageBubble from "./MessageBubble";
import { sendMessage, startNewChat, fetchChatHistory } from "../api/chatAPI";
import { TypingIndicator } from "./typingIndicator";

interface Message {
  role: "user" | "bot";
  content: string;
}

interface Chat {
  chat_id: string;
  title: string;
}


const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<{ chat_id: string; title: string }[]>([]);
  const [isTyping, setIsTyping] = useState<boolean>(false);

  useEffect(() => {
    loadChatHistory();
  }, []);

  const loadChatHistory = async () => {
    try {
      const history = await fetchChatHistory();
      setChatHistory(history);
    } catch (error) {
      console.error("Error loading chat history:", error);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);

    setInput("");

    try {
      setIsTyping(true);

      const response = await sendMessage(currentChatId, input);
      if (!currentChatId) {
        setCurrentChatId(response.chat_id);
        loadChatHistory();
      }

      const botMessage: Message = { role: "bot", content: response.response };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      };
    };

  const handleNewChat = async () => {
    try {
      const newChat = await startNewChat();
      setCurrentChatId(newChat.chat_id);
      setMessages([]);
      loadChatHistory();  
    } catch (error) {
      console.error("Error starting a new chat:", error);
    }
  };

  return (
    <div className="flex h-screen">
      <Sidebar 
        chats={chatHistory}
        onSelectChat={setCurrentChatId}
        onNewChat={handleNewChat} 
      />

      <div className="flex-1 flex flex-col bg-gray-800 text-gray-100">
        <div className="flex-1 overflow-y-auto p-4">
          {messages.map((msg, index) => (
            <MessageBubble key={index} role={msg.role} content={msg.content} />
          ))}
          {isTyping && (
            <MessageBubble role="bot" content={<TypingIndicator />} />
          )}
        </div>
        <div className="p-4 bg-gray-900 flex">
          <input
            className="flex-1 p-2 bg-gray-800 text-gray-200 rounded-lg border border-gray-700"
            placeholder="Type a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
          />
          <button
            onClick={handleSendMessage}
            className="ml-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface; 
