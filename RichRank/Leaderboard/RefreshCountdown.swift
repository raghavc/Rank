import Foundation
import Observation

@Observable
final class RefreshCountdown {
    private(set) var text: String = ""
    private var timer: Timer?

    private static let resetHour = 8 // 8 AM
    private static let timeZone = TimeZone(identifier: "America/New_York")!

    init() {
        update()
        timer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
            self?.update()
        }
    }

    deinit {
        timer?.invalidate()
    }

    private func update() {
        let now = Date()
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = Self.timeZone

        // Next 8 AM ET
        var components = cal.dateComponents([.year, .month, .day], from: now)
        components.hour = Self.resetHour
        components.minute = 0
        components.second = 0

        guard var target = cal.date(from: components) else {
            text = "--:--:--"
            return
        }

        // If we're already past 8 AM ET today, target tomorrow
        if target <= now {
            target = cal.date(byAdding: .day, value: 1, to: target) ?? target
        }

        let remaining = Int(target.timeIntervalSince(now))
        let h = remaining / 3600
        let m = (remaining % 3600) / 60
        let s = remaining % 60
        text = String(format: "%02d:%02d:%02d", h, m, s)
    }
}
