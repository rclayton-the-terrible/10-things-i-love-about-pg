import { Client } from 'pg';

async function main() {
  const client = new Client({
    user: 'postgres',
    password: '10thingsloveaboutpg',
    host: 'localhost',
    database: 'weather',
  });

  client.on('notification', (data) => {
    console.log('Notification:', data);
  });

  await client.connect();

  await client.query('LISTEN observations');
}

main().catch(console.error)
