import SwiftUI

/// Small pill that shows either a signed dollar delta (when |Δ| > $100) or a percent.
/// Mint for ≥ 0, coral for < 0.
struct DeltaPill: View {
    let amount: Decimal?    // pass nil when only pct is known (leaderboard list rows)
    let pct: Double

    private var isPositive: Bool {
        if let amount { return amount >= 0 }
        return pct >= 0
    }

    private var label: String {
        if let amount, abs(NSDecimalNumber(decimal: amount).doubleValue) > 100 {
            return RankFormatters.signedDollars(amount)
        }
        return RankFormatters.percent(pct)
    }

    private var arrow: String {
        isPositive ? "▲" : "▼"
    }

    var body: some View {
        HStack(spacing: 4) {
            Text(label)
            Text(arrow)
        }
        .font(.rankDelta)
        .foregroundStyle(isPositive ? Color.rankMint : Color.rankCoral)
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .background(
            Capsule().fill((isPositive ? Color.rankMint : Color.rankCoral).opacity(0.10))
        )
    }
}
