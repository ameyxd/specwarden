import { useState } from "react";

interface CounterProps {
  initial?: number;
  label?: string;
}

export function Counter({ initial = 0, label = "Count" }: CounterProps) {
  const [count, setCount] = useState(initial);

  return (
    <div className="counter">
      <span className="counter-label">{label}</span>
      <span className="counter-value">{count}</span>
      <div className="counter-controls">
        <button onClick={() => setCount((n) => n - 1)}>-</button>
        <button onClick={() => setCount((n) => n + 1)}>+</button>
        <button onClick={() => setCount(initial)}>Reset</button>
      </div>
    </div>
  );
}
