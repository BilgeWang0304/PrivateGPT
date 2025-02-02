import React from "react";
import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders the chatbot interface", () => {
  // Render the App component
  render(<App />);

  // Check if certain elements are rendered
  const inputElement = screen.getByPlaceholderText("Type your message...");
  expect(inputElement).toBeInTheDocument();

  const sendButton = screen.getByText(/send/i); // Case-insensitive match for "Send" button
  expect(sendButton).toBeInTheDocument();

  const chatContainer = screen.getByRole("textbox");
  expect(chatContainer).toBeInTheDocument();
});
