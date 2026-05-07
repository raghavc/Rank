import SwiftUI

extension Font {
    /// Big bold rank number.
    static let rankRankNumber = Font.system(size: 22, weight: .bold, design: .default)
    /// Big bold balance.
    static let rankBalance = Font.system(size: 18, weight: .semibold, design: .default)
    /// Anonymous-handle vibe.
    static let rankUsername = Font.system(size: 15, weight: .regular, design: .monospaced)
    /// Tagline / caption.
    static let rankCaption = Font.system(size: 13, weight: .regular, design: .default)
    /// Display-sized title (e.g. "Rank" on the welcome screen).
    static let rankDisplay = Font.system(size: 56, weight: .bold, design: .default)
    /// Section/screen headers.
    static let rankHeader = Font.system(size: 28, weight: .bold, design: .default)
    /// Pill labels.
    static let rankPill = Font.system(size: 13, weight: .semibold, design: .default)
    /// Delta pill text.
    static let rankDelta = Font.system(size: 12, weight: .semibold, design: .rounded)
}

struct PillButtonStyle: ButtonStyle {
    var filled: Bool = true

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 16, weight: .semibold, design: .default))
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .foregroundStyle(filled ? Color.white : Color.black)
            .background(
                Capsule(style: .continuous)
                    .fill(filled ? Color.black : Color.white)
            )
            .overlay(
                Capsule(style: .continuous)
                    .stroke(filled ? Color.clear : Color.rankBorder, lineWidth: 1)
            )
            .opacity(configuration.isPressed ? 0.85 : 1.0)
            .scaleEffect(configuration.isPressed ? 0.985 : 1.0)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}

extension ButtonStyle where Self == PillButtonStyle {
    static var rankPrimary: PillButtonStyle { PillButtonStyle(filled: true) }
    static var rankSecondary: PillButtonStyle { PillButtonStyle(filled: false) }
}
