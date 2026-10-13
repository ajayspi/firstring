const API_BASE = process.env.API_BASE || 'http://127.0.0.1:8000';
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || 'admin-token-12345';

const clinics = [
  { phone: '+919876543210', plan: 'free' },
  { phone: '+919876543211', plan: 'pro' },
  { phone: '+919876543212', plan: 'free' },
];

const outcomes = ['booking', 'voicemail', 'message', 'dropped'];

async function seed() {
  console.log('Seeding demo data...');

  // Register clinics
  for (const clinic of clinics) {
    const res = await fetch(`${API_BASE}/admin/clinics/${clinic.phone}/simulate-call`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ADMIN_TOKEN}`,
      },
      body: JSON.stringify({
        caller_phone: '+919000000000',
        outcome: 'booking',
        duration_min: 1,
      }),
    });
    if (!res.ok) throw new Error(`Failed to register clinic ${clinic.phone}`);
  }

  // Generate calls
  for (let i = 0; i < 50; i++) {
    const clinic = clinics[Math.floor(Math.random() * clinics.length)];
    const outcome = outcomes[Math.floor(Math.random() * outcomes.length)];
    const duration = Math.floor(Math.random() * 10) + 1;

    const res = await fetch(`${API_BASE}/admin/clinics/${clinic.phone}/simulate-call`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${ADMIN_TOKEN}`,
      },
      body: JSON.stringify({
        caller_phone: `+9190000000${i.toString().padStart(2, '0')}`,
        outcome,
        duration_min: duration,
      }),
    });
    if (!res.ok) throw new Error(`Failed to create call ${i}`);
  }

  console.log('Demo data seeded successfully!');
}

seed().catch(console.error);
