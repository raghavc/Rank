import Foundation

enum RankFormatters {
    static let currency: NumberFormatter = {
        let f = NumberFormatter()
        f.numberStyle = .currency
        f.currencyCode = "USD"
        f.maximumFractionDigits = 2
        f.minimumFractionDigits = 2
        return f
    }()

    static let signedCurrency: NumberFormatter = {
        let f = NumberFormatter()
        f.numberStyle = .currency
        f.currencyCode = "USD"
        f.maximumFractionDigits = 0
        f.minimumFractionDigits = 0
        f.positivePrefix = "+" + (f.currencySymbol ?? "$")
        return f
    }()

    static let integer: NumberFormatter = {
        let f = NumberFormatter()
        f.numberStyle = .decimal
        f.maximumFractionDigits = 0
        return f
    }()

    static func currency(_ d: Decimal) -> String {
        currency.string(from: d as NSDecimalNumber) ?? "$0"
    }

    static func signedDollars(_ d: Decimal) -> String {
        signedCurrency.string(from: d as NSDecimalNumber) ?? "$0"
    }

    static func rank(_ n: Int) -> String {
        "#" + (integer.string(from: NSNumber(value: n)) ?? "\(n)")
    }

    static func count(_ n: Int) -> String {
        integer.string(from: NSNumber(value: n)) ?? "\(n)"
    }

    static func percent(_ pct: Double) -> String {
        let signed = String(format: "%+.1f%%", pct)
        return signed
    }
}
