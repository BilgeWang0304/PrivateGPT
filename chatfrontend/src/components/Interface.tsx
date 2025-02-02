import React, { useEffect, useState } from "react";
import ChatSidebar from "./ChatSidebar";
import MessageBubble from "./MessageBubble";
import { sendMessage, sendMessageStream, startNewChat, uploadFile, fetchChatHistoryById, fetchChatHistory, queryFile  } from "../api/chatAPI";
import { TypingIndicator } from "./typingIndicator";
import { FaFileAlt, FaTimes } from "react-icons/fa"; 
import { AiOutlineWechatWork } from "react-icons/ai";

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
  const [chatHistory, setChatHistory] = useState<Chat[]>([]);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);


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
    setUploadedFile(null); // Reset file after sending
    setUploadedFileName(null);

    const textarea = document.querySelector("textarea");
      if (textarea) {
        textarea.style.height = "auto";
      }

    try {
      setIsTyping(true);

      const botMessage: Message = {
        role: "bot",
        content: "",
      };
      setMessages((prev) => [...prev, botMessage]);

      if (!uploadedFile) {
        // If no file uploaded, use normal chatbot logic
        const responseStream = await sendMessageStream(currentChatId, input);
        let fullResponse = "";
        for await (const chunk of responseStream) {
          fullResponse += chunk; // Append the chunk to the accumulated response
          console.log("Received chunk:", chunk); // Debug: Log each chunk

          setMessages((prev) =>
            prev.map((msg, idx) =>
              idx === prev.length - 1
                ? { ...msg, content: fullResponse }
                : msg
            )
          );
        }
        if (!currentChatId) {
          const { chat_id } = await sendMessage(currentChatId, input);
          setCurrentChatId(chat_id);
          await loadChatHistory();
        }
      } else {
        // If file is uploaded, treat it as a query to the uploaded file
        const response = await sendMessage(currentChatId, input); // Reuse same sendMessage function
        const botMessage: Message = {
          role: "bot",
          content: response.response.result,
        };
        setMessages((prev) => [...prev, botMessage]);
      }
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsTyping(false);
    }
  };

  const handleNewChat = async () => {
    setUploadedFile(null);
    setUploadedFileName(null);
    try {
      const newChat = await startNewChat();
      setCurrentChatId(newChat.chat_id);
      setMessages([]);
      await loadChatHistory();
    } catch (error) {
      console.error("Error starting a new chat:", error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files || event.target.files.length === 0) return;

    const file = event.target.files[0];
    setUploadedFile(file); 
    setUploadedFileName(file.name);
    try {
      const message = await uploadFile(file);
      alert(message); 
    } catch (error) {
      console.error("Error uploading file:", error);
    }
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setUploadedFileName(null);
  };

  const handleSelectChat = async (chatId: string) => {
    try {
      const chatMessages = await fetchChatHistoryById(chatId);
      setCurrentChatId(chatId);
      setMessages(chatMessages);
    } catch (error) {
      console.error("Error loading chat messages:", error);
    }
  };

  const handleChatDeleted = (chatId: string) => {
    setChatHistory((prev) => prev.filter((chat) => chat.chat_id !== chatId));
    if (currentChatId === chatId) {
      setCurrentChatId(null);
      setMessages([]);
    }
  };

  return (
    <div className="flex h-screen">
      <ChatSidebar
        chats={chatHistory}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onChatDeleted={handleChatDeleted}
        currentChatId={currentChatId}
      />

      <div className="flex-1 flex flex-col bg-gray-800 text-gray-100">
        <div className="flex-1 overflow-y-auto p-8">
        {messages.map((msg, index) => (
            <MessageBubble key={index} role={msg.role} content={msg.content} />
          ))}
          {isTyping && (
            <MessageBubble role="bot" content={<TypingIndicator />} />
          )}
        </div>
        {uploadedFile && (
          <div className="p-2 bg-gray-700 text-gray-300 flex items-center space-x-2 border-t border-gray-600">
            <FaFileAlt size={18} />
            <span>{uploadedFileName}</span>
            <button onClick={handleRemoveFile} className="text-red-500 hover:text-red-700">
              <FaTimes size={16} />
            </button>
          </div>
        )}
        <div className="p-4 bg-gray-900 flex">
          <label className="mr-4 cursor-pointer">
            <span className="text-blue-500 hover:text-blue-600 text-3xl font-bold">+</span>
            <input
              type="file"
              onChange={handleFileUpload}
              style={{ display: "none" }}
            />
          </label>
          <textarea
            className="flex-1 p-2 bg-gray-800 text-gray-200 rounded-lg border border-gray-700 resize-none shadow-sm"
            placeholder="Type a message..."
            value={input}
            rows={1}
            onChange={(e) => {
              setInput(e.target.value);

              const target = e.target as HTMLTextAreaElement;
              target.style.height = "auto"; 
              target.style.height = `${target.scrollHeight}px`; 
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault(); 
                handleSendMessage();
                const target = e.target as HTMLTextAreaElement;
                target.style.height = "auto";
              }
            }}
          ></textarea>
          <button
            onClick={handleSendMessage}
            className="ml-4 px-4 py-2 h-12 bg-blue-500 text-white text-lg rounded-lg hover:bg-blue-600"
          >
            Send
          </button>
        </div>
        <p className="text-center bg-gray-900 text-gray-300 text-sm mb-2">
          This Chatbot can make mistakes. Check important info.
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;
