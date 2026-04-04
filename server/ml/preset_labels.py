"""Preset label definitions with seed emails.

Each label ships with 10-12 diverse seed examples that cover the realistic
variety of emails in that category. The seeds are used to compute an initial
medoid so the label can match real emails immediately, without the user having
to manually select training examples.


Usage
-----
    from ml.preset_labels import build_preset_labels

    labels = build_preset_labels()   # dict[str, Label]
    # labels is ready to pass into process_email / find_best_label.
    # Persist however / wherever you choose — this module does no I/O.
"""

from app.models.label import Label
from ml.pipeline import seed_label

# ---------------------------------------------------------------------------
# Raw seed data: label name → list of (subject, body) tuples
# ---------------------------------------------------------------------------

PRESET_SEEDS: dict[str, list[tuple[str, str]]] = {

    "Receipts & Orders": [
        (
            "Your Amazon order has shipped (#112-3456789-0123456)",
            "Hello, your order of 'Anker USB-C Charging Cable (6ft, 3-Pack)' has "
            "shipped and is on its way. Estimated delivery: March 27. Track your "
            "package: [tracking link]. Order total: $18.99.",
        ),
        (
            "Receipt from Apple",
            "Thank you for your purchase. Invoice #: INV-20260325. Item: 1 × iCloud+ "
            "50 GB — $0.99. Billed to Visa ending in 4242. "
            "If you didn't make this purchase, contact Apple Support.",
        ),
        (
            "Your Instacart order is on its way!",
            "Your shopper Darius is heading to you now. Order total: $54.37 "
            "(including delivery fee and tip). Estimated arrival: 3:15 PM. "
            "View your order details and receipt.",
        ),
        (
            "Order Confirmation — DoorDash",
            "You placed an order from Chipotle Mexican Grill. Order #: DD-8821047. "
            "Items: Chicken Burrito Bowl, Chips & Guac, Lemonade. "
            "Subtotal: $19.45 + $3.99 delivery + $2.00 tip = $25.44.",
        ),
        (
            "Your Nike order is confirmed",
            "Thanks for your order! Order number: W9283761. Air Max 270 — Men's, "
            "Size 11, Black/White × 1 — $130.00. Estimated delivery: March 29–31. "
            "You'll get another email when your order ships.",
        ),
        (
            "Etsy order confirmation: Handmade ceramic mug",
            "Great news! Your order from PotteryByClara has been confirmed. "
            "Item: Speckled Sage Ceramic Mug. Order total: $34.00 + $6.50 shipping. "
            "Expected to ship within 3–5 business days.",
        ),
        (
            "Your package was delivered — USPS",
            "Your package has been delivered. Tracking #: 9400111899223756089012. "
            "Delivered to front door at 2:41 PM on March 25, 2026. "
            "If you did not receive your package, please contact the sender.",
        ),
        (
            "Uber Eats: Your order from McDonald's is confirmed",
            "Your order is being prepared. Estimated delivery: 25–35 min. "
            "Order summary: Big Mac Meal, 10pc McNuggets, Large Fries. "
            "Total charged: $22.18 including fees and tip.",
        ),
        (
            "Your Best Buy order is ready for pickup",
            "Good news! Your order #BBY-20260325-991 is ready for in-store pickup "
            "at Best Buy, 1 Infinite Loop, Cupertino. Item: Samsung 65\" QLED TV. "
            "Please bring your ID and order confirmation. Pickup available until 9 PM.",
        ),
        (
            "Shipping confirmation: Your Chewy order is on its way",
            "Your order has shipped! Items: Blue Buffalo Life Protection Formula "
            "Dog Food 30lb, Milk-Bone Dog Treats. Carrier: FedEx. "
            "Tracking #: 776491823710. Expected delivery: March 28.",
        ),
        (
            "Your Walmart order has been placed",
            "Order confirmed! Order #: 4829-10293-8812. Items: Bounty Paper Towels "
            "12-pack, Tide Pods 96ct, Febreze Air Freshener 3-pack. "
            "Pickup scheduled for March 26 between 2–3 PM. Order total: $47.83.",
        ),
        (
            "Receipt: Spotify Premium — March 2026",
            "Your payment was successful. Amount: $11.99. Plan: Spotify Premium "
            "Individual. Billing date: March 25, 2026. Next billing date: April 25, 2026. "
            "Payment method: Visa ending in 1234. View your receipt.",
        ),
    ],

    "Finance & Banking": [
        (
            "Your statement is ready — Chase Sapphire Preferred",
            "Your March statement is now available. Closing balance: $1,243.87. "
            "Minimum payment due: $35.00 by April 21. Log in to view your full "
            "statement and make a payment.",
        ),
        (
            "Low balance alert — Bank of America",
            "Your checking account balance has fallen below your $500 alert "
            "threshold. Current balance: $312.44 as of March 25, 2026. "
            "Transfer funds to avoid overdraft fees.",
        ),
        (
            "Your credit score changed — Experian",
            "Your credit score increased by 14 points. New score: 748 (Good). "
            "Key factors: on-time payments (Excellent), credit utilization 17%, "
            "0 derogatory marks. View your full credit report and score history →",
        ),
        (
            "You have a new deposit — Wells Fargo",
            "A direct deposit of $3,124.00 from EMPLOYER PAYROLL was posted to "
            "your checking account on March 25, 2026. "
            "Available balance: $4,801.22.",
        ),
        (
            "Payment reminder: Rent due March 28",
            "Hi, your rent payment of $2,150.00 is due in 3 days. Log in to "
            "your Zelle account or use the link below to pay your landlord. "
            "Late fees apply after the 5th of the month.",
        ),
        (
            "Your Robinhood portfolio update",
            "Your portfolio is down 2.3% today. Current value: $14,582.19. "
            "Notable movers: TSLA -4.1%, AAPL +0.8%. View your full portfolio "
            "breakdown and recent transactions.",
        ),
        (
            "Large purchase alert: $892.00 at Best Buy — Citi Card",
            "A transaction of $892.00 was made at Best Buy on March 25, 2026 "
            "using your Citi Double Cash card ending in 5678. "
            "If you did not make this purchase, call us immediately.",
        ),
        (
            "Your tax documents are ready — Fidelity",
            "Your 2025 tax documents are now available in your Fidelity account. "
            "Documents ready: 1099-DIV, 1099-B, 1099-INT. "
            "Download them from your account documents section before April 15.",
        ),
        (
            "Wire transfer confirmation — $1,500.00 sent",
            "Your wire transfer of $1,500.00 to James Harrington has been sent. "
            "Reference #: WR-20260325-4421. Funds should arrive within 1–2 business days. "
            "Contact us if you did not authorize this transfer.",
        ),
        (
            "Your Geico auto insurance renewal — payment due April 1",
            "Your 6-month auto insurance policy renews on April 1, 2026. "
            "Renewal premium: $612.00 for two vehicles. Your current policy expires March 31. "
            "Log in to update your payment method or review your coverage options.",
        ),
        (
            "Autopay scheduled: $238.00 — Discover Card",
            "Your autopay of $238.00 (minimum payment) is scheduled to process "
            "on March 28 from your checking account ending in 9900. "
            "Current statement balance: $1,188.44.",
        ),
        (
            "Your 401(k) quarterly statement — Vanguard",
            "Your Q1 2026 account statement is now available. "
            "Account balance: $47,382.14. Contributions this quarter: $2,100.00. "
            "Employer match: $1,050.00. Investment gain/loss: +$1,843.22. View statement →",
        ),
    ],

    "Travel": [
        (
            "Your United flight confirmation — SFO → JFK",
            "Booking confirmed! Confirmation #: UABC12. Flight UA 234, "
            "departing SFO April 5 at 8:15 AM, arriving JFK at 4:42 PM. "
            "Passenger: Kevin Huang. Check in online starting 24 hours before departure.",
        ),
        (
            "Airbnb reservation confirmed — Austin, TX",
            "Your trip is booked! You're staying at 'Cozy East Austin Bungalow' "
            "from April 14–18. Host: Maria. Check-in: 3:00 PM. "
            "Reservation code: HMAB8X. Total charged: $487.00.",
        ),
        (
            "Your Marriott Bonvoy reservation",
            "Reservation confirmed at New York Marriott Downtown. Arrival: April 5. "
            "Departure: April 8. Room: King Deluxe, non-smoking. "
            "Confirmation #: 98234751. Rate: $249/night + taxes.",
        ),
        (
            "Trip itinerary: Paris, April 20–27",
            "Here is your full travel itinerary. Outbound: AA 100 LAX→CDG Apr 20 "
            "10:50 PM. Return: AA 101 CDG→LAX Apr 27 11:30 AM. Hotel: Le Marais "
            "Boutique — Apr 21–27. Car rental: Hertz confirmation #HZ9921.",
        ),
        (
            "Your Lyft ride receipt",
            "Thanks for riding with Lyft! Date: March 25, 2026. Pickup: 123 Main St. "
            "Drop-off: SFO Terminal 2. Distance: 14.3 miles. Total: $38.72 "
            "(including tolls). Driver: James L. ★★★★★",
        ),
        (
            "Your Delta flight is tomorrow — Check in now",
            "Your flight DL 409 from ATL to LAX departs tomorrow at 6:50 AM. "
            "Check in now to choose your seat and get your boarding pass. "
            "Gate information will be available 2 hours before departure.",
        ),
        (
            "Rental car confirmation — Enterprise",
            "Your rental is confirmed! Pickup: Denver International Airport, "
            "April 10 at 11:00 AM. Return: April 14 at 11:00 AM. "
            "Vehicle: Intermediate SUV (Toyota RAV4 or similar). Total: $218.40.",
        ),
        (
            "Your VRBO booking is confirmed",
            "You're all set for your stay! Property: 'Lakefront Cabin Retreat — "
            "Lake Tahoe'. Dates: April 28 – May 2. Guests: 4. "
            "Confirmation #: VR-7738291. Total paid: $1,240.00.",
        ),
        (
            "TSA PreCheck renewal — application received",
            "We've received your TSA PreCheck renewal application. "
            "Application #: TSA-20260325-88421. Your current membership expires "
            "June 14, 2026. You'll be notified once your renewal is processed.",
        ),
        (
            "Your Amtrak ticket — Boston South Station → New York Penn",
            "Booking confirmed! Train: Acela 2151. Departure: April 8 at 7:00 AM. "
            "Arrival: April 8 at 10:58 AM. Seat: Car 3, Seat 14A (Business Class). "
            "E-ticket attached. Confirmation #: AMTK-5582910.",
        ),
        (
            "Flight delay notification — AA 204",
            "Your American Airlines flight AA 204 (ORD → MIA) has been delayed. "
            "New departure time: 4:45 PM (originally 2:30 PM). Gate: B22. "
            "We apologize for the inconvenience. Rebooking options available in the app.",
        ),
    ],

    "Work": [
        (
            "Re: Q2 roadmap review — Thursday 2pm",
            "Hi team, just confirming the Q2 roadmap sync for Thursday at 2 PM PST. "
            "Agenda: review OKRs, prioritize backlog, assign owners. "
            "Please come prepared with your team's updates. Zoom link attached.",
        ),
        (
            "Jira: [PROJECT-412] Bug: Login fails on iOS 17.4 — assigned to you",
            "Kevin Huang, you have been assigned issue PROJECT-412. "
            "Summary: Users on iOS 17.4 cannot complete login via OAuth. "
            "Priority: High. Reporter: Sarah Chen. Due: March 28. View issue →",
        ),
        (
            "GitHub: Pull request review requested",
            "daniela-dev requested your review on pull request #88: "
            "'feat: add export to CSV on analytics dashboard'. Repository: acme/backend. "
            "View the diff and leave your feedback on GitHub.",
        ),
        (
            "Re: Production incident — payments service down",
            "Hi Kevin, we're seeing a spike in 500 errors on the payments service since 2:15 PM. "
            "Looks like it might be related to your last deploy. Can you roll back or investigate ASAP? "
            "Looping in Sam and the on-call team. Datadog shows ~40% error rate. — Alex",
        ),
        (
            "Zoom: Meeting recording available — All Hands March 2026",
            "The recording for 'All Hands — March 2026' is now available. "
            "Duration: 52 minutes. Recorded by: Jane (Host). "
            "View or download the recording within 30 days.",
        ),
        (
            "Notion: Kevin, you were mentioned in 'Sprint Planning Notes'",
            "You were mentioned by Alex in the page 'Sprint Planning Notes — Week 13'. "
            "Excerpt: '@Kevin please own the API rate-limiting task this sprint.' "
            "Open in Notion →",
        ),
        (
            "Google Calendar: Performance review with manager — tomorrow at 10 AM",
            "Reminder: You have a meeting tomorrow. Event: Q1 Performance Review. "
            "Time: March 26 at 10:00 AM PST. With: Lisa Park (Engineering Manager). "
            "Location: Google Meet. Join link included.",
        ),
        (
            "DocuSign: Please sign 'Consulting Agreement — March 2026'",
            "Kevin Huang, you have been sent a document to review and sign. "
            "Document: Consulting Agreement — March 2026. Sender: Legal Team, Acme Corp. "
            "Please complete signing by March 30, 2026.",
        ),
        (
            "Your expense report has been approved — Concur",
            "Your expense report 'Austin Sales Conference — March 2026' has been approved. "
            "Total approved: $1,204.50 (flights, hotel, meals). Reimbursement will be "
            "included in your next paycheck or direct-deposited within 3–5 business days.",
        ),
        (
            "Your onboarding checklist — Day 1 at Acme Corp",
            "Welcome to Acme Corp! Here's your onboarding checklist for your first week. "
            "Action items: Complete I-9 verification, set up your dev environment, "
            "join #engineering on Slack, and schedule a 1:1 with your manager.",
        ),
        (
            "Linear: Issue assigned — 'Refactor auth middleware' [ENG-881]",
            "You've been assigned ENG-881: Refactor auth middleware to support "
            "multi-tenant token validation. Priority: Medium. Cycle: Sprint 22. "
            "Estimate: 3 points. View in Linear →",
        ),
        (
            "Re: Offer letter — Senior Software Engineer",
            "Hi Kevin, please find attached your official offer letter for the "
            "Senior Software Engineer role at Acme Corp. Start date: April 14, 2026. "
            "Compensation: $175,000 base + equity. Please sign and return by March 31.",
        ),
    ],

    "Social": [
        (
            "Twitter/X: @techcrunch mentioned you in a reply",
            "@techcrunch replied to your tweet: 'Great point on LLM latency — "
            "completely agree with your take.' Your tweet now has 47 likes and "
            "12 retweets. View the conversation →",
        ),
        (
            "Instagram: sophia_creates and 14 others liked your photo",
            "sophia_creates, mark.dev, and 13 others liked your photo. "
            "You also have 3 new followers this week. "
            "See your latest activity in the Instagram app.",
        ),
        (
            "Facebook: Marcus Rodriguez sent you a friend request",
            "Marcus Rodriguez sent you a friend request. "
            "You have 12 mutual friends including Sarah Chen, David Kim, and others. "
            "Accept or decline in the Facebook app.",
        ),
        (
            "TikTok: Your video has 10,000 views",
            "Congratulations! Your video reached 10,000 views. "
            "Likes: 842, Comments: 134, Shares: 291. "
            "See detailed analytics and who's engaging with your content.",
        ),
        (
            "Discord: You have unread messages in 3 servers",
            "You have unread messages in: #general (Indie Hackers — 14 messages), "
            "#announcements (Next.js Community — 2 messages), "
            "#random (Friends Group — 8 messages). Open Discord to catch up.",
        ),
        (
            "LinkedIn: James Park accepted your connection request",
            "James Park, Senior Product Manager at Stripe, accepted your connection "
            "request. You now have 512 connections. Send James a message to start "
            "the conversation.",
        ),
        (
            "Snapchat: You have 3 unopened snaps",
            "You have unopened snaps from Maya, Jordan, and +1 more. "
            "Don't let them expire — open them before they disappear! "
            "Open Snapchat to view your snaps and streaks.",
        ),
        (
            "Instagram: maya_j sent you a direct message",
            "maya_j sent you a DM: 'omg did you see this?? 😭' "
            "Tap to reply in the Instagram app. "
            "You also have 2 unread message requests from new accounts.",
        ),
        (
            "Facebook: Jordan tagged you in a photo",
            "Jordan tagged you in a photo at Griffith Observatory. "
            "3 people have reacted to this photo: Sarah, Mike, and +1 more. "
            "See the photo and manage your tag →",
        ),
        (
            "Reddit: u/devguru99 replied to your comment in r/cscareerquestions",
            "u/devguru99 replied to your comment: 'Totally agree — the system design "
            "round is usually the hardest part for new grads.' "
            "Your comment has 14 upvotes. View the full thread →",
        ),
        (
            "Twitter/X: 5 new followers today",
            "You have 5 new followers: @ml_research, @jane_codes, @kevin_builds, "
            "@techdigest, and 1 more. Check out their profiles and follow back. "
            "Your tweet from yesterday now has 142 impressions.",
        ),
        (
            "LinkedIn: Sofia Reyes sent you a message",
            "Sofia Reyes (UX Designer at Figma) sent you a LinkedIn message: "
            "'Hey! I saw your post about design systems — really resonated. "
            "Would love to connect and chat sometime.' Reply in LinkedIn →",
        ),
    ],

    "Promotions & Deals": [
        (
            "Flash Sale: 40% off sitewide — Today Only",
            "Don't miss out! Our biggest sale of the season starts NOW. "
            "40% off everything in our store — no code needed, discount applied "
            "at checkout. Sale ends tonight at midnight. Shop now →",
        ),
        (
            "Your exclusive offer: $20 off your next order",
            "Hi Kevin, we haven't seen you in a while — here's $20 off your next "
            "purchase of $60 or more. Use code COMEBACK20 at checkout. "
            "Offer expires April 5, 2026.",
        ),
        (
            "Amazon: Limited-time deal on items you viewed",
            "Items you recently viewed are on sale. "
            "Sony WH-1000XM5 Headphones: was $349.99, now $229.99 (34% off). "
            "Deal ends in 6 hours. Add to cart before it's gone.",
        ),
        (
            "Earn double points this weekend — Starbucks Rewards",
            "Star Days are back! Earn 2× stars on every purchase this Saturday "
            "and Sunday. Redeem for free drinks and food. "
            "Visit any Starbucks location or order on the app.",
        ),
        (
            "Your loyalty reward is ready to use",
            "You've unlocked a $15 reward! You've earned enough points to claim "
            "your loyalty reward. Use it on your next in-store or online purchase. "
            "Reward expires in 30 days. View your account →",
        ),
        (
            "Members only: Early access to our summer sale",
            "As a valued member, you get first access to our Summer Sale — "
            "24 hours before it opens to the public. Up to 60% off select styles. "
            "Early access ends March 27 at 11:59 PM.",
        ),
        (
            "Groupon: 3 deals expiring soon near you",
            "Don't let these deals expire! Oakley Spa & Wellness — 50% off massage "
            "($45 value for $22). The Burger Joint — $20 for $10. "
            "SF Museum of Modern Art — 2-for-1 admission. View all →",
        ),
        (
            "We matched a lower price on your recent order",
            "Great news! We found a lower price on an item from your recent order. "
            "Item: Bose QuietComfort 45. Original price: $279.00. "
            "New price: $229.00. A refund of $50.00 has been applied to your card.",
        ),
        (
            "Last chance: Your cart is about to expire",
            "You left items in your cart and they're almost gone! "
            "Nike Dri-FIT Running Shorts (qty: 1) — only 3 left in stock. "
            "Complete your purchase now before someone else grabs them.",
        ),
        (
            "Costco: Exclusive member savings this month",
            "March member-only savings are here. Highlights: "
            "Kirkland Signature Olive Oil 2L — $12.99 (save $4). "
            "Dyson V15 Vacuum — $499.99 (save $100). Valid through March 31.",
        ),
        (
            "You have $8.47 in unused cashback — Rakuten",
            "You've earned cashback from your recent purchases! "
            "Nike.com: $3.20. Booking.com: $5.27. Total available: $8.47. "
            "Cash out via PayPal or check on your next Big Fat Check date.",
        ),
        (
            "Walk into spring. New arrivals just dropped — Crocs",
            "The season's freshest styles are here. Shop the new Classic Clog "
            "colorways and limited-edition collabs before they sell out. "
            "Free shipping on orders over $50. Explore new arrivals →",
        ),
        (
            "New season, new fits. Shop the Spring Collection — Levi's",
            "Fresh denim for a fresh start. Introducing the Spring 2026 Collection — "
            "new cuts, washes, and silhouettes. Shop men's and women's styles now. "
            "Members get free returns. Find your fit →",
        ),
        (
            "Your next obsession just arrived — ASOS New In",
            "Over 500 new styles added this week. From going-out tops to "
            "everyday sneakers, we've got your wardrobe covered. "
            "Shop new in now — new drops every day.",
        ),
    ],

    "Account & Security": [
        (
            "Reset your password",
            "We received a request to reset the password for your account associated "
            "with this email. Click the link below to reset your password. This link "
            "expires in 15 minutes. If you didn't request this, ignore this email.",
        ),
        (
            "New sign-in to your Google Account",
            "Your Google Account was just signed in from a new device. "
            "Device: MacBook Pro, San Francisco, CA. Time: March 25, 2026, 9:14 AM. "
            "If this was you, no action needed. If not, secure your account now.",
        ),
        (
            "Your two-factor authentication code",
            "Your verification code is: 847 291. This code expires in 10 minutes. "
            "Do not share this code with anyone. If you didn't request this, "
            "please change your password immediately.",
        ),
        (
            "Action required: Verify your email address",
            "Thanks for signing up! Please verify your email address to activate "
            "your account. Click the button below within 24 hours. "
            "If you didn't create an account with us, you can safely ignore this.",
        ),
        (
            "Unusual activity detected on your account",
            "We noticed unusual sign-in activity on your account. For your security, "
            "we've temporarily locked your account. Please verify your identity "
            "to regain access. This lock will expire in 24 hours.",
        ),
        (
            "Blocked sign-in attempt from Moscow, Russia",
            "Someone tried to sign in to your account from an unrecognized location: "
            "Moscow, Russia at 3:42 AM. We blocked this attempt. "
            "If this wasn't you, change your password and review your recent activity immediately.",
        ),
        (
            "Your Apple ID was used to sign in on a new device",
            "Your Apple ID was used to sign in to iCloud on a new iPhone 16 Pro. "
            "Location: San Francisco, CA. Time: March 25, 2026 at 8:52 AM. "
            "If this is you, no action is needed. If not, go to appleid.apple.com.",
        ),
        (
            "Security alert: Password changed on your Microsoft account",
            "Your Microsoft account password was recently changed. "
            "If you made this change, you can disregard this email. "
            "If you didn't change your password, please secure your account immediately.",
        ),
        (
            "Important: Your info was found in a data breach",
            "We detected your email address in a recent data breach from DataCorp (March 2026). "
            "Exposed information: email address, phone number, hashed password. "
            "We recommend changing your password on any site where you reuse these credentials.",
        ),
        (
            "Dropbox: A new device was linked to your account",
            "A new device was linked to your Dropbox account. "
            "Device: Chrome on Windows 11, Chicago, IL. Time: March 25 at 3:17 PM. "
            "Not you? Remove this device and update your password.",
        ),
        (
            "Your two-factor authentication backup codes",
            "Two-factor authentication has been enabled on your account. "
            "Save these one-time backup codes in a secure location. Each code can only be used once. "
            "If you did not enable two-factor authentication, secure your account immediately.",
        ),
        (
            "Your account access has been revoked — action required",
            "Your access to the shared workspace has been removed by an administrator. "
            "If you believe this was done in error, contact your account admin. "
            "All active sessions have been signed out and your permissions revoked.",
        ),
    ],

    "Recruiting & Interviews": [
        (
            "Application received — Software Engineer New Grad 2026 (Requisition #REQ-SWE-NG-0412)",
            "Thank you for submitting your application through Greenhouse for the "
            "Software Engineer, New Grad 2026 role at Stripe. Our talent acquisition team "
            "will review your resume and reach out if your background aligns with our "
            "current headcount. Requisition #: REQ-SWE-NG-2026-0412.",
        ),
        (
            "HackerRank Online Assessment — Amazon SDE Intern (Algorithms & Data Structures)",
            "You have been invited to complete a HackerRank online assessment for the "
            "SDE Intern role at Amazon. The assessment contains 2 algorithmic problems "
            "covering dynamic programming and graph traversal. Time limit: 90 minutes. "
            "Per our NDA, do not share problem statements during or after the assessment.",
        ),
        (
            "University Recruiting — Google SWE New Grad Cohort, reaching out re: headcount",
            "Hi Kyle, I'm a university recruiter at Google and came across your profile. "
            "We have open headcount for our New Grad SWE cohort starting July 2026 on the "
            "Search Infrastructure team. Would you be available for a 20-minute exploratory "
            "call? I can send a Calendly link. — Priya, University Talent Acquisition",
        ),
        (
            "Technical Phone Screen Scheduled — Meta, CoderPad, April 8 at 2 PM PST",
            "Your 45-minute technical phone screen with Meta has been scheduled. "
            "Interviewer: David Chen (Staff Engineer, Infra). Format: one LeetCode-style "
            "coding problem on CoderPad. You will receive the CoderPad session link "
            "15 minutes before your interview. Reply with any scheduling conflicts.",
        ),
        (
            "Virtual Onsite Confirmed — Apple SWE Internship, 4 rounds: DSA, systems design, behavioral",
            "Your virtual onsite interview loop with Apple is confirmed for April 12. "
            "Round 1 (10:00 AM): Data Structures & Algorithms. "
            "Round 2 (11:00 AM): Systems Design. Round 3 (1:00 PM): Behavioral. "
            "Round 4 (2:00 PM): Hiring Manager. Each session is 45 minutes via Zoom.",
        ),
        (
            "Offer Letter — Software Engineer Intern, Airbnb Summer 2026 · $60/hr + RSU",
            "Dear Kyle, we are delighted to extend an offer for Software Engineer Intern "
            "at Airbnb for Summer 2026. Compensation: $60.00/hr. Housing stipend: $2,500/mo. "
            "Relocation: $5,000 one-time. Countersign via DocuSign by April 20. "
            "Offer contingent on successful completion of a background check.",
        ),
        (
            "Interview loop decision — not moving forward, Software Engineer New Grad, Uber",
            "Hi Kyle, thank you for completing the interview loop for the Software Engineer "
            "New Grad role at Uber. After careful evaluation of your performance across all "
            "rounds, we have decided to move forward with other candidates whose qualifications "
            "more closely match our current requirements. We will retain your resume on file.",
        ),
        (
            "Return Offer — Full-Time Software Engineer, Palantir · $145k base + $50k RSU, 4-yr vest",
            "Hi Kyle, following your internship we are pleased to extend a full-time return offer "
            "for Software Engineer at Palantir. Total compensation: $145,000 base + $50,000 RSU "
            "grant (4-year vest, 1-year cliff) + $15,000 signing bonus. "
            "Please indicate acceptance or declination by May 1.",
        ),
        (
            "Background Check Initiated — Sterling on behalf of LinkedIn, employment history required",
            "LinkedIn has initiated a pre-employment background check through Sterling. "
            "Log in to Sterling's candidate portal to consent, verify your identity, and "
            "submit your employment history. Estimated turnaround: 3–5 business days. "
            "Do not begin employment until your background check has cleared.",
        ),
        (
            "Karat Interview on behalf of Twitch — Engineering Fundamentals, 60 min coding round",
            "Your Karat technical interview on behalf of Twitch is confirmed for April 9 "
            "at 3:00 PM PST. Interview type: Engineering Fundamentals (coding). "
            "Duration: 60 minutes. You will solve algorithm problems while narrating your "
            "thought process. Your interviewer will be a Karat-certified engineer. "
            "Join at: karat.com/interview/your-session.",
        ),
        (
            "New Grad SWE job alert — Stripe, Figma, Databricks, 8 roles matching your profile",
            "Hi Kyle, 8 new Software Engineer roles match your Glassdoor job alert. "
            "Highlights: Software Engineer II at Stripe (NYC) — Python/Go, 0–2 yrs exp. "
            "Frontend Engineer at Figma (SF) — React, TypeScript, new grad welcome. "
            "SWE New Grad at Databricks (Remote). Apply directly through Glassdoor.",
        ),
        (
            "New Grad Offer — SWE II, Microsoft Azure Cohort 2026A · $135k + $70k RSU",
            "Hi Kyle, congratulations on completing your interview loop. We are pleased to "
            "invite you to join Microsoft's New Graduate Software Engineer program, Cohort 2026A. "
            "Role: SWE II, Azure Compute. Location: Redmond, WA (hybrid). "
            "Compensation: $135,000 base + $70,000 RSU (4-year vest, 1-year cliff) + "
            "$20,000 signing bonus. Offer expires April 30, 2026.",
        ),
    ],
}


# ---------------------------------------------------------------------------
# Builder: computes embeddings + medoid for each label, returns Label objects
# ---------------------------------------------------------------------------

def build_preset_labels() -> dict[str, Label]:
    """Return a dict of seeded Label objects ready for the ML pipeline.
    """
    labels: dict[str, Label] = {}

    for name, seeds in PRESET_SEEDS.items():
        seeded = seed_label(seeds)
        labels[name] = Label(
            name=name,
            type="system",
            **seeded,
        )

    return labels
