# Store Intelligence Platform - Frontend

A modern, responsive dashboard for the Store Intelligence Platform built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

- ✅ **Real-time Analytics Dashboard**
  - Store metrics (entries, exits, occupancy)
  - Conversion funnel visualization
  - Anomaly detection alerts
  - Health monitoring

- ✅ **Modern Tech Stack**
  - Next.js 14 (App Router)
  - TypeScript
  - Tailwind CSS
  - Recharts for data visualization
  - Axios for API calls

- ✅ **Production-Ready**
  - Responsive design
  - Auto-refresh (30s interval)
  - Error handling
  - Loading states
  - Type-safe API client

## Prerequisites

- Node.js 18+ or 20+
- npm or yarn
- Backend API running (see main README)

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env.local` file:

```bash
# Local development (backend on localhost:8000)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Or point to your Render deployment
# NEXT_PUBLIC_API_URL=https://your-service.onrender.com
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
frontend/
├── src/
│   ├── app/                # Next.js app directory
│   │   ├── globals.css    # Global styles
│   │   ├── layout.tsx     # Root layout
│   │   └── page.tsx       # Home page
│   ├── components/        # React components
│   │   ├── Dashboard.tsx           # Main dashboard
│   │   ├── Sidebar.tsx            # Navigation sidebar
│   │   ├── MetricsCards.tsx       # Metrics display
│   │   ├── ConversionFunnelChart.tsx  # Funnel visualization
│   │   ├── AnomaliesTable.tsx     # Anomaly alerts
│   │   └── HealthIndicator.tsx    # API health status
│   └── lib/              # Utilities and API client
│       ├── api.ts        # API client (axios)
│       ├── types.ts      # TypeScript types
│       └── utils.ts      # Helper functions
├── public/               # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## Available Scripts

```bash
npm run dev          # Start development server (port 3000)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
```

## API Integration

The frontend connects to your FastAPI backend using the API client in `src/lib/api.ts`.

### Endpoints Used

- `GET /health` - Health check
- `GET /stores/{id}/metrics` - Store metrics
- `GET /stores/{id}/funnel` - Conversion funnel
- `GET /stores/{id}/anomalies` - Anomaly detection
- `GET /stores/{id}/heatmap` - Movement heatmap (future)
- `POST /events/ingest` - Event ingestion (future)

## Deployment to Vercel

### Option 1: Via Vercel Dashboard (Recommended)

1. **Push to GitHub**
   ```bash
   git add frontend/
   git commit -m "Add frontend dashboard"
   git push origin main
   ```

2. **Import to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New" → "Project"
   - Import your GitHub repository
   - Configure:
     - **Framework Preset**: Next.js
     - **Root Directory**: `frontend`
     - **Build Command**: `npm run build`
     - **Output Directory**: (leave default)

3. **Add Environment Variable**
   - Go to Settings → Environment Variables
   - Add:
     - **Name**: `NEXT_PUBLIC_API_URL`
     - **Value**: `https://your-service.onrender.com`
     - **Environment**: Production, Preview, Development

4. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Get your URL: `https://your-project.vercel.app`

### Option 2: Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy from frontend directory
cd frontend
vercel

# Follow prompts:
# - Set up new project? Yes
# - Link to existing project? No
# - Project name: store-intelligence-dashboard
# - Directory: ./
# - Override settings? No

# Deploy to production
vercel --prod
```

### Environment Variables for Vercel

Set these in your Vercel project settings:

| Variable | Value | Description |
|----------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://your-service.onrender.com` | Backend API URL |

## Development Tips

### Hot Reload

The development server supports hot reload. Changes to components will reflect immediately.

### Type Safety

TypeScript types for all API responses are defined in `src/lib/types.ts`. Update these if you modify the backend API.

### Styling

Uses Tailwind CSS utility classes. Customize colors in `tailwind.config.ts`.

### API Client

The API client (`src/lib/api.ts`) includes:
- Request/response interceptors
- Error handling
- Type-safe methods
- 30s timeout

## Customization

### Change Primary Color

Edit `tailwind.config.ts`:

```typescript
colors: {
  primary: {
    // Your color palette
    500: '#your-color',
  },
}
```

### Add New Store

Edit `src/components/Sidebar.tsx`:

```typescript
const stores = [
  { id: 'store_003', name: 'Store 003', location: 'New Location' },
  // ...
]
```

### Modify Auto-Refresh Interval

Edit `src/components/Dashboard.tsx`:

```typescript
// Change from 30000 (30s) to your preferred interval
const interval = setInterval(fetchData, 60000) // 60s
```

## Performance

- **Build Size**: ~500KB (optimized)
- **First Load**: ~2s (on Vercel)
- **API Response**: 100-500ms (depends on backend)
- **Auto-refresh**: 30s interval

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### API Connection Issues

If you see "Failed to fetch data":

1. Check backend is running
2. Verify `NEXT_PUBLIC_API_URL` is correct
3. Check CORS settings on backend (already configured)
4. Open browser DevTools → Network tab to see error

### Build Errors

```bash
# Clear cache and rebuild
rm -rf .next
npm run build
```

### Type Errors

```bash
# Check types
npm run type-check
```

## Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Heatmap visualization
- [ ] Event ingestion form
- [ ] Advanced filtering
- [ ] Date range selector
- [ ] Export to CSV/PDF
- [ ] User authentication
- [ ] Multi-store comparison
- [ ] Mobile app (React Native)

## License

Part of the Store Intelligence Platform project.

---

**Built with ❤️ using Next.js 14**
