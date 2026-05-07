import SwiftUI

extension Color {
    /// Soft mint green for positive deltas.
    static let rankMint = Color(red: 0x00 / 255.0, green: 0xC8 / 255.0, blue: 0x96 / 255.0)
    /// Soft coral for negative deltas.
    static let rankCoral = Color(red: 0xFF / 255.0, green: 0x6B / 255.0, blue: 0x6B / 255.0)
    /// Pure white background.
    static let rankBackground = Color.white
    /// 8% black hairline border.
    static let rankBorder = Color.black.opacity(0.08)
    /// Subtle muted grey for captions.
    static let rankMuted = Color.black.opacity(0.45)
    /// Fill behind subtle pills (toggle, etc.) — frosted-glass-ish.
    static let rankPillFill = Color.black.opacity(0.04)
    /// Terminal board background.
    static let rankTerminalCanvas = Color.white
    /// Thin terminal row highlight.
    static let rankTerminalRow = Color.black.opacity(0.035)
    /// Primary board text.
    static let rankTerminalText = Color.black.opacity(0.82)
    /// Hairline rule color.
    static let rankTerminalRule = Color.black.opacity(0.10)
}
