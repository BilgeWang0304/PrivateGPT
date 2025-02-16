import React from "react";
import { useTheme } from "./themeContext";

export const TypingIndicator: React.FC = () => {
  const { isDarkMode } = useTheme();

  return (
    <div className="flex space-x-1">
      <div 
        className={`w-2 h-2 rounded-full animate-bounce ${isDarkMode ? "bg-gray-400" : "bg-gray-600"}`} 
        style={{ animationDelay: "0s" }}
      ></div>
      <div 
        className={`w-2 h-2 rounded-full animate-bounce ${isDarkMode ? "bg-gray-400" : "bg-gray-600"}`} 
        style={{ animationDelay: "0.2s" }}
      ></div>
      <div 
        className={`w-2 h-2 rounded-full animate-bounce ${isDarkMode ? "bg-gray-400" : "bg-gray-600"}`} 
        style={{ animationDelay: "0.4s" }}
      ></div>
    </div>
  );
};