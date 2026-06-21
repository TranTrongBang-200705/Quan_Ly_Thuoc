import React from "react";
import { createRoot } from "react-dom/client";
import { Toaster } from "react-hot-toast";
import App from "./App";
import "./app.css";
import "./styles/clinical.css";

createRoot(document.getElementById("root")).render(
  <>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 4000,
        style: {
          fontFamily: "'Inter', sans-serif",
          fontSize: "14px",
          borderRadius: "14px",
          padding: "12px 16px",
          boxShadow: "0 8px 32px rgba(15, 23, 42, 0.10)",
        },
        success: {
          iconTheme: { primary: "#14b8a6", secondary: "#fff" },
        },
        error: {
          iconTheme: { primary: "#ef4444", secondary: "#fff" },
        },
      }}
    />
  </>
);
