export default function HomeLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <div style={{ display: "flex", height: "100vh" }}>{children}</div>;
}
