import Link from "next/link";

export default function NotFound() {
  return (
    <div
      style={{
        padding: "48px 24px",
        textAlign: "center",
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <h1>404</h1>
      <p>Page not found</p>
      <Link href="/">Go home</Link>
    </div>
  );
}
