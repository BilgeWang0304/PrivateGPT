import React from "react";
import ChatInterface from "./components/Interface";
import { ThemeProvider } from "./components/themeContext";
import "./App.css"

const App: React.FC = () => {
    return (
        <ThemeProvider>
            <ChatInterface />
        </ThemeProvider>
    )
};

export default App;

