const BASE_URL = "http://127.0.0.1:8000";

interface ChatResponse {
    chat_id: string | null;
    response: {
      query: string;
      result: string;
    };
}

interface ChatHistory {
    chat_id: string;
    title: string;
}

interface Message {
  role: "user" | "bot";
  content: string;
}

export const sendMessage = async (chat_id: string | null, message: string): Promise<ChatResponse> => {
    try {
        const response = await fetch(`${BASE_URL}/chat/`, {  
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            chat_id: chat_id || null,
            message: message.trim(),
           }),
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

export const sendMessageStream = async function* (
  chat_id: string | null,
  message: string
): AsyncGenerator<string, void, unknown> {
  try {
    const response = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        chat_id: chat_id || null,
        message: message.trim(),
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to send message for streaming.");
    }
    
    const reader = response.body?.getReader();
    const decoder = new TextDecoder("utf-8");

    if (!reader) {
      throw new Error("Failed to get response reader.");
    }

    let done = false;

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;

      if (value) {
        const chunk = decoder.decode(value, { stream: true });
        yield chunk; // Emit each chunk of the response
      }
    }
  } catch (error) {
    console.error("Streaming error:", error);
    throw error;
  }
};

export const startNewChat = async (): Promise<ChatResponse> => {
    try {
      const response = await fetch(`${BASE_URL}/chat/new_chat`, {  
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
      const response = await fetch(`${BASE_URL}/history`);  
  
      if (!response.ok) {
        throw new Error("Failed to fetch chat history.");
      }
  
      const data = await response.json();
      console.log("Fetched chat history:", data); 
      return data;
    } catch (error) {
      console.error("Error fetching chat history:", error);
      throw error;
    }
};

export const fetchChatHistoryById = async (chatId: string): Promise<Message[]> => {
  try {
    const response = await fetch(`${BASE_URL}/history/${chatId}`);  

    if (!response.ok) {
      throw new Error("Failed to fetch chat history.");
    }

    const data = await response.json();
    return data.messages;
  } catch (error) {
    console.error("Error fetching chat history:", error);
    throw error;
  }
};

export const uploadFile = async (chat_id: string, file: File): Promise<string> => {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${BASE_URL}/upload/${chat_id}`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error("Failed to upload the file.");
    }

    const data = await response.json();
    return data.message || "File uploaded successfully.";
  } catch (error) {
    console.error("File upload error:", error);
    return "Failed to upload the file.";
  }
};


export const deleteChat = async (chatId: string): Promise<void> => {
  try {
    const response = await fetch(`${BASE_URL}/history/${chatId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error("Failed to delete the chat.");
    }

    console.log(`Chat ${chatId} deleted successfully.`);
  } catch (error) {
    console.error("Error deleting chat:", error);
    throw error;
  }
};

export const renameChat = async (chatId: string, newTitle: string): Promise<string> => {
  try {
    const response = await fetch(`${BASE_URL}/history/${chatId}/rename`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title: newTitle }),
    });

    if (!response.ok) {
      throw new Error("Failed to rename the chat.");
    }

    const data = await response.json();
    return data.message || "Chat renamed successfully.";
  } catch (error) {
    console.error("Error renaming chat:", error);
    throw error;
  }
}