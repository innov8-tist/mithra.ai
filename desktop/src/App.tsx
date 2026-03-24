import { useState } from "react";
import reactLogo from "./assets/react.svg";
import { invoke } from "@tauri-apps/api/core";

function App() {
  const [greetMsg, setGreetMsg] = useState("");
  const [name, setName] = useState("");

  async function greet() {
    setGreetMsg(await invoke("greet", { name }));
  }

  return (
    <main className="flex flex-col items-center justify-center h-screen bg-gray-900 text-white p-8">
      <h1 className="text-4xl font-bold mb-8">Welcome to Tauri + React</h1>

      <div className="flex gap-8 mb-6">
        <a href="https://vite.dev" target="_blank" className="transition-transform hover:scale-110">
          <img src="/vite.svg" className="w-24 h-24" alt="Vite logo" />
        </a>
        <a href="https://tauri.app" target="_blank" className="transition-transform hover:scale-110">
          <img src="/tauri.svg" className="w-24 h-24" alt="Tauri logo" />
        </a>
        <a href="https://react.dev" target="_blank" className="transition-transform hover:scale-110">
          <img src={reactLogo} className="w-24 h-24" alt="React logo" />
        </a>
      </div>
      <p className="text-gray-400 mb-8">Click on the Tauri, Vite, and React logos to learn more.</p>

      <form
        className="flex gap-4 mb-6"
        onSubmit={(e) => {
          e.preventDefault();
          greet();
        }}
      >
        <input
          id="greet-input"
          onChange={(e) => setName(e.currentTarget.value)}
          placeholder="Enter a name..."
          className="px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button 
          type="submit"
          className="px-6 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900"
        >
          Greet
        </button>
      </form>
      <p className="text-lg text-green-400 font-medium">{greetMsg}</p>
    </main>
  );
}

export default App;
