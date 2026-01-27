import React from "react";
import ReactDOM from "react-dom/client";
import FormApp from "./FormApp";

const rootElement = document.getElementById("root");

if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<FormApp />);
} else {
  console.error('Не найден элемент с id="root" для FormApp');
}