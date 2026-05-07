import SwiftUI

struct LeaderboardRow: View {
    let entry: LeaderboardEntry
    var highlight: Bool = false

    var body: some View {
        HStack(spacing: 12) {
            Text(RankFormatters.rank(entry.rank))
                .font(.rankRankNumber)
                .foregroundStyle(.black)
                .frame(width: 78, alignment: .leading)

            Text(entry.username)
                .font(.rankUsername)
                .foregroundStyle(.black)
                .lineLimit(1)
                .truncationMode(.tail)

            Spacer(minLength: 8)

            VStack(alignment: .trailing, spacing: 4) {
                Text(RankFormatters.currency(entry.balance))
                    .font(.rankBalance)
                    .foregroundStyle(.black)

                DeltaPill(amount: nil, pct: entry.deltaPct)
            }
        }
        .padding(.vertical, 12)
        .padding(.horizontal, 12)
        .background(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .fill(highlight ? Color.rankPillFill : Color.clear)
        )
    }
}
