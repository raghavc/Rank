import SwiftUI

struct MyRankCard: View {
    let username: String
    let me: LeaderboardMe

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                Text(rankText)
                    .font(.rankHeader)
                    .foregroundStyle(.black)

                Text("of " + RankFormatters.count(me.totalUsers))
                    .font(.rankCaption)
                    .foregroundStyle(Color.rankMuted)
                    .padding(.bottom, 4)

                Spacer()

                DeltaPill(amount: me.deltaAmount, pct: me.deltaPct)
            }

            HStack(spacing: 12) {
                Text(username)
                    .font(.rankUsername)
                    .foregroundStyle(Color.rankMuted)
                Spacer()
                Text(RankFormatters.currency(me.balance))
                    .font(.rankBalance)
                    .foregroundStyle(.black)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 16)
        .background(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(Color.rankBorder, lineWidth: 1)
        )
    }

    private var rankText: String {
        guard let rank = me.rank else { return "—" }
        return RankFormatters.rank(rank)
    }
}
