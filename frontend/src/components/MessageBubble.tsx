import React from "react";

interface MessageBubbleProps {
  role: "user" | "bot"; // Role of the sender: user or bot
  content: string | React.ReactNode; // The actual message text
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ role, content }) => {
  return (
    <div
      className={`flex ${
        role === "user" ? "justify-end" : "justify-start"
      } mb-4`}
    >
      <div
        className={`max-w-md px-4 py-2 rounded-lg text-sm ${
          role === "user"
            ? "bg-blue-500 text-white"
            : "bg-gray-200 text-gray-900"
        }`}
      >
        {content}
      </div>
    </div>
  );
};

export default MessageBubble;
