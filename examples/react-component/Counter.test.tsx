import { render, screen, fireEvent } from "@testing-library/react";
import { Counter } from "./Counter";

test("reset button restores the initial value", () => {
  render(<Counter initial={5} />);
  fireEvent.click(screen.getByText("+"));
  fireEvent.click(screen.getByText("+"));
  expect(screen.getByText("7")).toBeInTheDocument();
  fireEvent.click(screen.getByText("Reset"));
  expect(screen.getByText("5")).toBeInTheDocument();
});
