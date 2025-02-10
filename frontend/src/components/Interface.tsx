import React, { useEffect, useState } from "react";
import ChatSidebar from "./ChatSidebar";
import MessageBubble from "./MessageBubble";
import { sendMessage, sendMessageStream, startNewChat, uploadFile, fetchChatHistoryById, fetchChatHistory  } from "../api/chatAPI";
import { TypingIndicator } from "./typingIndicator";
import { FaFileAlt, FaTimes, FaCheck } from "react-icons/fa"; 

interface Message {
  role: "user" | "bot";
  content: string;
}

interface Chat {
  chat_id: string;
  title: string;
}

interface ChatInterfaceState {
  uploadedFiles: { [key: string]: string | null }; 
}

const ProgressCircle = ({ progress, isDone }: { progress: number; isDone: boolean }) => (
  <div className="relative w-6 h-6 ml-2">
    <svg className="w-full h-full transform -rotate-90">
      <circle
        cx="50%"
        cy="50%"
        r="8"
        fill="none"
        className="stroke-current text-gray-400"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle
        cx="50%"
        cy="50%"
        r="8"
        fill="none"
        className={`stroke-current ${isDone ? 'text-green-500' : 'text-blue-500'}`}
        strokeWidth="2"
        strokeLinecap="round"
        strokeDasharray={`${2 * Math.PI * 8}`}
        strokeDashoffset={`${2 * Math.PI * 8 * (1 - progress)}`}
        style={{ transition: 'stroke-dashoffset 0.3s ease' }}
      />
    </svg>
    {isDone && (
      <FaCheck className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-green-500 text-xs" />
    )}
  </div>
);

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<Chat[]>([]);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<{ [key: string]: string[] }>(() => {
    const savedFiles = localStorage.getItem('uploadedFiles');
    return savedFiles ? JSON.parse(savedFiles) : {};
  });
  const [uploadingFiles, setUploadingFiles] = useState<{ [key: string]: boolean }>({});
  const [uploadProgress, setUploadProgress] = useState<{ 
    [key: string]: { 
      progress: number; 
      status: 'uploading' | 'done' | 'error' 
    } 
  }>({});

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

  useEffect(() => {
    localStorage.setItem('uploadedFiles', JSON.stringify(uploadedFiles));
  }, [uploadedFiles]);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setUploadedFile(null); 
    setUploadedFileName(null);

    const textarea = document.querySelector("textarea");
      if (textarea) {
        textarea.style.height = "auto";
      }

      try {
        setIsTyping(true);
        
        // Add a temporary bot response placeholder
        setMessages((prev) => [...prev, { role: "bot", content: "" }]);

        let fullResponse = "";

        // **Use streaming for both normal and file-based queries**
        console.log(`Sending query ${uploadedFile ? "with file" : "without file"}...`);
        const responseStream = await sendMessageStream(currentChatId, input);

        for await (const chunk of responseStream) {
            fullResponse += chunk; // Append chunks as they arrive
            console.log("Received chunk:", chunk);

            // Update the last bot message in real-time
            setMessages((prev) =>
                prev.map((msg, idx) =>
                    idx === prev.length - 1
                        ? { ...msg, content: fullResponse }
                        : msg
                )
            );
        }

        // Final update to the last bot message
        setMessages((prev) =>
            prev.map((msg, idx) =>
                idx === prev.length - 1 ? { ...msg, content: fullResponse } : msg
            )
        );

        // Ensure the chatbot correctly associates the chat session with the file
        if (!currentChatId) {
            const { chat_id } = await sendMessage(currentChatId, input);
            setCurrentChatId(chat_id);
            await loadChatHistory();
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
    if (!event.target.files?.length) return;
    const file = event.target.files[0];
    const fileName = file.name;
  
    if (!currentChatId) {
      alert("Please start a new chat before uploading a file.");
      return;
    }
  
    // Immediately show file with loading state
    setUploadedFiles(prev => ({
      ...prev,
      [currentChatId]: [...(prev[currentChatId] || []), fileName]
    }));
    
    setUploadProgress(prev => ({
      ...prev,
      [fileName]: { progress: 0, status: 'uploading' }
    }));
  
    try {
      // Simulate progress (replace with real progress events if available)
      const interval = setInterval(() => {
        setUploadProgress(prev => ({
          ...prev,
          [fileName]: {
            ...prev[fileName],
            progress: Math.min(prev[fileName].progress + 0.1, 0.9)
          }
        }));
      }, 200);
  
      await uploadFile(currentChatId, file);
  
      // Finalize progress
      setUploadProgress(prev => ({
        ...prev,
        [fileName]: { progress: 1, status: 'done' }
      }));
      
      clearInterval(interval);
    } catch (error) {
      console.error("Upload failed:", error);
      setUploadProgress(prev => ({
        ...prev,
        [fileName]: { progress: 0, status: 'error' }
      }));
      // Remove file from list after delay
      setTimeout(() => {
        setUploadedFiles(prev => ({
          ...prev,
          [currentChatId]: (prev[currentChatId] || []).filter(name => name !== fileName)
        }));
      }, 2000);
    } finally {
      event.target.value = '';
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
    setUploadedFiles(prev => {
      const newFiles = { ...prev };
      delete newFiles[chatId];
      return newFiles;
    });

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

      <div className="flex-1 flex flex-col  bg-gray-800 text-gray-100">
        <div className="flex-1 overflow-y-auto p-8">
        {messages.map((msg, index) => (
            <MessageBubble key={index} role={msg.role} content={msg.content} />
          ))}
          {isTyping && (
            <MessageBubble role="bot" content={<TypingIndicator />} />
          )}
        </div>
        {currentChatId && (uploadedFiles[currentChatId] || []).map((fileName, index) => {
          const progressData = uploadProgress[fileName] || { progress: 0, status: 'uploading' };
          
          return (
            <div key={index} className="p-2 bg-gray-700 text-gray-300 flex items-center space-x-2 border-t border-gray-600">
              <FaFileAlt size={18} />
              <span className="flex-1">{fileName}</span>
              
              {progressData.status === 'error' ? (
                <span className="text-red-500 text-sm">Upload Failed</span>
              ) : (
                <ProgressCircle 
                  progress={progressData.progress} 
                  isDone={progressData.status === 'done'}
                />
              )}
              
              <button 
                onClick={() => {
                  setUploadedFiles(prev => ({
                    ...prev,
                    [currentChatId]: (prev[currentChatId] || []).filter((_, i) => i !== index)
                  }));
                  setUploadProgress(prev => {
                    const newState = { ...prev };
                    delete newState[fileName];
                    return newState;
                  });
                }}
                className="text-red-500 hover:text-red-700 ml-2"
              >
                <FaTimes size={16} />
              </button>
            </div>
          );
        })}
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
            className="text-lg flex-1 p-2 bg-gray-800 text-gray-200 rounded-lg border border-gray-700 resize-none shadow-sm"
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