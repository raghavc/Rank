import SwiftUI

struct LeaderboardToggle: View {
    @Binding var scope: LeaderboardScope

    var body: some View {
        HStack(spacing: 4) {
            ForEach(LeaderboardScope.allCases) { option in
                Button {
                    withAnimation(.easeInOut(duration: 0.18)) { scope = option }
                } label: {
                    Text(option.displayName)
                        .font(.rankPill)
                        .foregroundStyle(scope == option ? .white : .black)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(
                            Capsule(style: .continuous)
                                .fill(scope == option ? Color.black : Color.clear)
                        )
                }
                .buttonStyle(.plain)
            }
        }
        .padding(4)
        .background(
            Capsule(style: .continuous).fill(Color.rankPillFill)
        )
    }
}

#Preview {
    @Previewable @State var s: LeaderboardScope = .global
    return LeaderboardToggle(scope: $s).padding()
}
