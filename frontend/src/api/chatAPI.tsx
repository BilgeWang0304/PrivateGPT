const BASE_URL = "http://127.0.0.1:8000";

interface ChatResponse {
    chat_id: string;
    response: string;
}

interface ChatHistory {
    chat_id: string;
    title: string;
}

export const sendMessage = async (chat_id: string | null, message: string): Promise<ChatResponse> => {
    try {
        const response = await fetch(`${BASE_URL}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ chat_id, message }),
        });
    
        if (!response.ok) {
          throw new Error("Failed to send message to the backend.");
        }
    
        return await response.json();
      } catch (error) {
        console.error("Error sending message:", error);
        throw error;
    }
};

export const startNewChat = async (): Promise<ChatResponse> => {
    try {
      const response = await fetch(`${BASE_URL}/new_chat`, {
        method: "POST",
      });
  
      if (!response.ok) {
        throw new Error("Failed to start a new chat.");
      }
  
      return await response.json();
    } catch (error) {
      console.error("Error starting new chat:", error);
      throw error;
    }
};

export const fetchChatHistory = async (): Promise<ChatHistory[]> => {
    try {
      const response = await fetch(`${BASE_URL}/chats`);
  
      if (!response.ok) {
        throw new Error("Failed to fetch chat history.");
      }
  
      return await response.json();
    } catch (error) {
      console.error("Error fetching chat history:", error);
      throw error;
    }
};