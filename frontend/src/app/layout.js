import "./globals.css";

export const metadata = {
  title: "MentorBoard — Student Dashboard",
  description: "Mentor portal for managing student batches, counseling sessions, and academic records at Bannari Amman Institute of Technology.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
