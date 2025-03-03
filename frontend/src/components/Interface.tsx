import React, { useEffect, useState } from "react";
import ChatSidebar from "./ChatSidebar";
import MessageBubble from "./MessageBubble";
import { sendMessage, sendMessageStream, startNewChat, uploadFile, fetchChatHistoryById, fetchChatHistory  } from "../api/chatAPI";
import { TypingIndicator } from "./typingIndicator";
import { FaFileAlt, FaTimes, FaCheck } from "react-icons/fa"; 
import { useTheme } from "./themeContext";

interface Message {
  role: "user" | "bot";
  content: string;
}

interface Chat {
  chat_id: string;
  title: string;
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
  const { isDarkMode, toggleTheme } = useTheme();
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
  const [uploadProgress, setUploadProgress] = useState<{ 
    [key: string]: { 
      progress: number; 
      status: 'uploading' | 'done' | 'error' 
    } 
  }>({});

  const isArabic = (text: string): boolean => {
    const arabicRegex = /[\u0600-\u06FF]/;
    return arabicRegex.test(text);
  }

  const [isInputArabic, setIsInputArabic] = useState(false);

  useEffect(() => {
    setIsInputArabic(isArabic(input));
  }, [input]);

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
        
        setMessages((prev) => [...prev, { role: "bot", content: "" }]);

        let fullResponse = "";


        console.log(`Sending query ${uploadedFile ? "with file" : "without file"}...`);
        const responseStream = await sendMessageStream(currentChatId, input);

        for await (const chunk of responseStream) {
            fullResponse += chunk; 
            console.log("Received chunk:", chunk);


            setMessages((prev) =>
                prev.map((msg, idx) =>
                    idx === prev.length - 1
                        ? { ...msg, content: fullResponse }
                        : msg
                )
            );
        }

        setMessages((prev) =>
            prev.map((msg, idx) =>
                idx === prev.length - 1 ? { ...msg, content: fullResponse } : msg
            )
        );

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
  
    setUploadedFiles(prev => ({
      ...prev,
      [currentChatId]: [...(prev[currentChatId] || []), fileName]
    }));
    
    setUploadProgress(prev => ({
      ...prev,
      [fileName]: { progress: 0, status: 'uploading' }
    }));
  
    try {
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

      <div className={`flex-1 flex flex-col  ${isDarkMode ? "bg-gray-800 text-gray-100" : "bg-gray-200 text-gray-800"}`}>
        <div className="flex-1 overflow-y-auto p-8">
        {messages.map((msg, index) => (
            <MessageBubble key={index} role={msg.role} content={msg.content} />
          ))}
          {isTyping && (
            <MessageBubble role="bot" content={<TypingIndicator />} />
          )}
        </div>
        {/* Input Area */}
        <div className={`p-4 pr-20 pl-10 pb-0 ${isDarkMode ? "bg-gray-800" : "bg-gray-200"}`}>
          <div className="relative">
            <textarea
              className={`w-full p-4 pr-24 pl-16 ${
                isDarkMode ? "bg-gray-900 border-gray-700 text-gray-200" : "bg-white border-gray-200 text-gray-800"
              } rounded-lg border border-gray-700 resize-none shadow-lg`}
              placeholder="Type a message..."
              value={input}
              rows={3}
              style={{
                minHeight: '6rem',
                maxHeight: '12rem',
                overflowY: 'auto',
                direction: isInputArabic ? 'rtl' : 'ltr', 
                textAlign: isInputArabic ? 'right' : 'left', 
              }}
              onChange={(e) => {
                setInput(e.target.value);
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                const newHeight = Math.min(
                  Math.max(target.scrollHeight, 96),
                  192
                );
                target.style.height = `${newHeight}px`;
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            ></textarea>

            {/* Left side buttons */}
            <div className="absolute left-3 bottom-4 flex items-center gap-2">
              <label className="cursor-pointer">
                <span className="text-gray-400 hover:text-blue-500 transition-colors">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 4V20M20 12H4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </span>
                <input
                  type="file"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>

            {/* Right side send button */}
            <div className="absolute right-3 bottom-4">
              <button
                onClick={handleSendMessage}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
                disabled={!input.trim()}
              >
                Send
              </button>
            </div>
          </div>

          {/* Uploaded files list */}
          {currentChatId && (uploadedFiles[currentChatId] || []).map((fileName, index) => {
            const progressData = uploadProgress[fileName] || { progress: 0, status: 'uploading' };
            
            return (
              <div key={index} className={`mt-2 p-2 ${isDarkMode ? "bg-gray-700 text-gray-300" : "bg-white text-gray-800"} flex items-center space-x-2 rounded-lg`}>
                <FaFileAlt size={16} />
                <span className="flex-1 text-sm">{fileName}</span>
                
                {progressData.status === 'error' ? (
                  <span className="text-red-500 text-xs">Failed</span>
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
                  className="text-red-400 hover:text-red-500 ml-2"
                >
                  <FaTimes size={14} />
                </button>
              </div>
            );
          })}
        </div>
        <p className={`text-center ${isDarkMode ? "bg-gray-800 text-gray-300" : "bg-gray-200 text-gray-800"} text-sm mb-6`}>
          This Chatbot can make mistakes. Check important info.
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;