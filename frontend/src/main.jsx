import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./app.jsx";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    {/* BrowserRouter: 앱 전체에서 주소(URL) 기반 화면 전환을 가능하게 함 */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
