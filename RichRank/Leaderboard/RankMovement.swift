import SwiftUI

enum RankMovement {
    case up
    case down
    case flat
    case unknown

    static func from(current: Int, previous: Int?) -> RankMovement {
        guard let previous else { return .unknown }
        if current < previous { return .up }
        if current > previous { return .down }
        return .flat
    }
}

struct RankMovementGlyph: View {
    let movement: RankMovement

    var body: some View {
        Group {
            switch movement {
            case .up:
                Image(systemName: "arrow.up")
                    .font(.system(size: 11, weight: .bold))
                    .foregroundStyle(Color.rankMint)
            case .down:
                Image(systemName: "arrow.down")
                    .font(.system(size: 11, weight: .bold))
                    .foregroundStyle(Color.rankCoral)
            case .flat, .unknown:
                Text("–")
                    .font(.system(size: 13, weight: .medium, design: .monospaced))
                    .foregroundStyle(Color.rankMuted)
            }
        }
        .frame(width: 18, alignment: .center)
    }
}
