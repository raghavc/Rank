import SwiftUI

struct LeaderboardToggle: View {
    @Binding var scope: LeaderboardScope

    var body: some View {
        HStack(spacing: 4) {
            ForEach(LeaderboardScope.allCases) { option in
                Button {
                    withAnimation(.easeInOut(duration: 0.18)) { scope = option }
                } label: {
                    Text(option.displayName.uppercased())
                        .font(.system(size: 12, weight: .semibold, design: .monospaced))
                        .foregroundStyle(
                            scope == option
                                ? Color.rankTerminalCanvas
                                : Color.rankTerminalText.opacity(0.75)
                        )
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(
                            Capsule(style: .continuous)
                                .fill(scope == option ? Color.rankTerminalText : Color.clear)
                        )
                }
                .buttonStyle(.plain)
            }
        }
        .padding(4)
        .background(
            Capsule(style: .continuous)
                .stroke(Color.rankTerminalRule, lineWidth: 1)
        )
        .background(
            Capsule(style: .continuous)
                .fill(Color.rankPillFill)
        )
    }
}

#Preview {
    @Previewable @State var s: LeaderboardScope = .global
    return LeaderboardToggle(scope: $s).padding()
}
