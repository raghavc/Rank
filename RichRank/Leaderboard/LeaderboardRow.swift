import SwiftUI

enum LeaderboardTerminalColumns {
    static let movementWidth: CGFloat = 18
    static let rankWidth: CGFloat = 52
}

struct LeaderboardRow: View {
    let entry: LeaderboardEntry
    var highlight: Bool = false

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 10) {
                RankMovementGlyph(
                    movement: RankMovement.from(current: entry.rank, previous: entry.previousRank)
                )

                Text(RankFormatters.rank(entry.rank))
                    .font(.system(size: 17, weight: .semibold, design: .monospaced))
                    .foregroundStyle(Color.rankTerminalText)
                    .frame(width: LeaderboardTerminalColumns.rankWidth, alignment: .trailing)

                Text(entry.username)
                    .font(.system(size: 16, weight: .medium, design: .monospaced))
                    .foregroundStyle(Color.rankTerminalText.opacity(highlight ? 1.0 : 0.88))
                    .lineLimit(1)
                    .truncationMode(.tail)

                Text("|")
                    .font(.system(size: 14, weight: .regular, design: .monospaced))
                    .foregroundStyle(Color.rankTerminalRule)

                Spacer(minLength: 8)

                Text(RankFormatters.currency(entry.balance))
                    .font(.system(size: 16, weight: .semibold, design: .monospaced))
                    .foregroundStyle(Color.rankTerminalText)
                    .monospacedDigit()
            }
            .padding(.horizontal, 16)
            .frame(maxWidth: .infinity, minHeight: 54, alignment: .center)
            .background(highlight ? Color.rankTerminalRow : Color.clear)

            Rectangle()
                .fill(Color.rankTerminalRule)
                .frame(height: 1)
        }
        .background(Color.rankTerminalCanvas)
    }
}
