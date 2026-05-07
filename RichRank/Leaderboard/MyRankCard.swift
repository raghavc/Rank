import SwiftUI

struct MyRankCard: View {
    let username: String
    let me: LeaderboardMe

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 10) {
                Text(username)
                    .font(.system(size: 18, weight: .semibold, design: .monospaced))
                    .foregroundStyle(Color.rankTerminalText)
                    .lineLimit(1)
                    .truncationMode(.tail)

                Text("|")
                    .font(.system(size: 14, weight: .regular, design: .monospaced))
                    .foregroundStyle(Color.rankTerminalRule)

                Spacer()

                Text(RankFormatters.currency(me.balance))
                    .font(.system(size: 18, weight: .semibold, design: .monospaced))
                    .foregroundStyle(Color.rankTerminalText)
                    .monospacedDigit()
            }

            HStack(spacing: 8) {
                if let rank = me.rank {
                    RankMovementGlyph(
                        movement: RankMovement.from(current: rank, previous: me.previousRank)
                    )
                }

                Text(rankText)
                    .font(.system(size: 13, weight: .regular, design: .monospaced))
                    .foregroundStyle(Color.rankTerminalText.opacity(0.48))

                Text("·")
                    .font(.system(size: 13, weight: .regular, design: .monospaced))
                    .foregroundStyle(Color.rankTerminalText.opacity(0.32))

                Text(RankFormatters.count(me.totalUsers) + " users")
                    .font(.system(size: 13, weight: .regular, design: .monospaced))
                    .foregroundStyle(Color.rankTerminalText.opacity(0.48))

                Spacer()
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(Color.rankTerminalCanvas)
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(Color.rankTerminalRule)
                .frame(height: 1)
        }
    }

    private var rankText: String {
        guard let rank = me.rank else { return "—" }
        return RankFormatters.rank(rank)
    }
}
