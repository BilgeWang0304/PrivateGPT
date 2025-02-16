import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { FaRegLightbulb } from "react-icons/fa";
import { useTheme } from "./themeContext";

interface MessageBubbleProps {
  role: "user" | "bot";
  content: string | React.ReactNode;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ role, content }) => {
  const { isDarkMode } = useTheme();
  
  if (content === null || content === undefined) {
    return null;
  }

  // Check if content is a string
  const isStringContent = typeof content === "string";
  
  let thinkContent = "";
  let mainContent = content;

  if (isStringContent) {
    const thinkMatch = (content as string).match(/<think>([\s\S]*?)<\/think>/);
    thinkContent = thinkMatch ? thinkMatch[1].trim() : "";
    mainContent = thinkMatch 
      ? (content as string).replace(thinkMatch[0], "").trim()
      : content;
  }

  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"} mb-6`}>
      <div
        className={`px-4 py-2 rounded-xl text-xl relative ${
          role === "user"
            ? isDarkMode
              ? "bg-blue-500 bg-opacity-90 text-white max-w-3xl"
              : "bg-blue-500 text-white max-w-3xl"
            : isDarkMode
              ? "bg-gray-700 bg-opacity-60 text-gray-200 max-w-5xl"
              : "bg-gray-300  text-gray-800 max-w-5xl"
        }`}
      >
        {thinkContent && (
          <div className={`mb-4 p-3 pl-6 border-l-4 text-lg relative 
            ${isDarkMode ? "border-gray-400 bg-gray-700 bg-opacity-50 text-gray-300" : "border-gray-600 bg-gray-200 text-gray-800"}`}>
            <span className=" text-lg font-bold flex items-center space-x-2">
              <FaRegLightbulb className={`${isDarkMode ? "text-yellow-300" : "text-yellow-500"} mr-2`} size={20} />
              Thinking Phase
            </span>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {thinkContent.replace(/\n/g, "  \n")}
            </ReactMarkdown>
          </div>
        )}

        {isStringContent ? (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ node, ...props }) => <h1 className="text-2xl font-bold mb-2" {...props} />,
              h2: ({ node, ...props }) => <h2 className="text-xl font-bold mb-2" {...props} />,
              h3: ({ node, ...props }) => <h3 className="text-lg font-semibold mb-2" {...props} />,
              p: ({ node, ...props }) => <p className="mb-2 leading-relaxed" {...props} />,
              strong: ({ node, ...props }) => <strong className="font-bold" {...props} />,
              ul: ({ node, ...props }) => <ul className="list-disc list-inside ml-5 mb-2" {...props} />,
              li: ({ node, ...props }) => <li className="mb-1" {...props} />,
              a: ({ node, ...props }) => (
                <a className="text-blue-500 underline" target="_blank" rel="noopener noreferrer" {...props} />
              ),
              br: () => <br />,
            }}
          >
            {(mainContent as string).replace(/\n/g, "  \n")}
          </ReactMarkdown>
        ) : (
          mainContent
        )}
      </div>
    </div>
  );
};

export default MessageBubble;