import "./Highlight.css";

export default function Highlight({ variant = "success", children }) {
  return <span className={`highlight highlight--${variant}`}>{children}</span>;
}
