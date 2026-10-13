import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'FirstRing — AI Receptionist for Indian Clinics & Salons',
  description:
    'Never miss another booking. An AI receptionist that answers after-hours calls in Hindi and English, books straight into your calendar, and WhatsApps you the details.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
