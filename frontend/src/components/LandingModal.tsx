interface LandingModalProps {
  onDismiss: () => void;
}

export default function LandingModal({ onDismiss }: LandingModalProps) {
  return (
    <div className="landing-overlay" role="dialog" aria-modal="true" aria-label="Welcome">
      <div className="landing-dim" />
      <div className="landing-card">
        <h1 className="landing-headline">Earth Club Sandwich</h1>
        <p className="landing-purpose">
          A round-the-world travelogue — following the route, stop by stop.
        </p>

        <div className="landing-section">
          <h2 className="landing-section-title">The Trip</h2>
          <p className="landing-body">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
            incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
            quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
            Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
            eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident,
            sunt in culpa qui officia deserunt mollit anim id est laborum.
          </p>
        </div>

        <div className="landing-section">
          <h2 className="landing-section-title">How to Browse</h2>
          <ul className="landing-list">
            <li>Click a <strong>flag pin</strong> on the map to expand a region</li>
            <li>Scroll the <strong>sidebar</strong> to see all stops in order</li>
            <li>Click a <strong>stop tile</strong> or map marker to open the detail view</li>
          </ul>
        </div>

        <div className="landing-callout">
          <p>
            Keeping up from home? The sidebar shows the full itinerary — visited stops,
            planned stops, and everything in between.
          </p>
        </div>

        <button className="landing-dismiss-btn" onClick={onDismiss}>
          Start Exploring
        </button>
      </div>
    </div>
  );
}
