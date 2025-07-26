import '../styles/globals.css';
import FloatingDashboard from '../components/FloatingDashboard';

export const metadata = {
  title: 'Invoice Processing App',
  description: 'AI-powered invoice processing with real-time dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {children}
        <FloatingDashboard />
      </body>
    </html>
  )
}
