import SwiftUI

struct TerminalTickerScroll: View {
    var entries: [LeaderboardEntry]
    var highlightUsername: String?
    var rowHeight: CGFloat = 54
    var threshold: Int = 10

    @Environment(\.scenePhase) private var scenePhase
    @State private var anchorOffset: CGFloat = 0
    @State private var dragOffset: CGFloat = 0
    @State private var dragStartAnchorOffset: CGFloat = 0
    @State private var isInteracting = false
    @State private var autoStartDate = Date()

    private var rowUnitHeight: CGFloat { rowHeight + 1 }

    var body: some View {
        if entries.count < threshold || scenePhase != .active {
            VStack(spacing: 0) {
                ForEach(entries) { entry in
                    LeaderboardRow(
                        entry: entry,
                        highlight: highlightUsername == entry.username
                    )
                }
            }
            .frame(maxWidth: .infinity, alignment: .topLeading)
        } else {
            tickerViewport
        }
    }

    private var tickerViewport: some View {
        let listHeight = CGFloat(entries.count) * rowUnitHeight

        return GeometryReader { geo in
            let viewportHeight = max(geo.size.height, rowUnitHeight * 3)

            TimelineView(.animation(minimumInterval: 1.0 / 60.0, paused: false)) { timeline in
                let elapsed = timeline.date.timeIntervalSince(autoStartDate)
                let speed: CGFloat = 24
                let autoDistance = isInteracting ? 0 : CGFloat(elapsed) * speed
                let cycleOffset = wrappedOffset(anchorOffset + dragOffset - autoDistance, listHeight: listHeight)

                VStack(spacing: 0) {
                    ForEach(0..<(entries.count * 3), id: \.self) { index in
                        LeaderboardRow(
                            entry: entries[index % entries.count],
                            highlight: highlightUsername == entries[index % entries.count].username
                        )
                    }
                }
                .offset(y: -listHeight - cycleOffset)
                .frame(width: geo.size.width, height: viewportHeight, alignment: .top)
                .clipped()
            }
            .contentShape(Rectangle())
            .gesture(
                DragGesture(minimumDistance: 2)
                    .onChanged { value in
                        if !isInteracting {
                            isInteracting = true
                            dragStartAnchorOffset = wrappedOffset(
                                anchorOffset - CGFloat(Date().timeIntervalSince(autoStartDate)) * 24,
                                listHeight: listHeight
                            )
                            dragOffset = 0
                        }
                        dragOffset = -value.translation.height
                    }
                    .onEnded { value in
                        let finalOffset = dragStartAnchorOffset - value.translation.height
                        anchorOffset = wrappedOffset(finalOffset, listHeight: listHeight)
                        dragOffset = 0
                        isInteracting = false
                        autoStartDate = Date()
                    }
            )
            .onAppear {
                anchorOffset = wrappedOffset(anchorOffset, listHeight: listHeight)
                autoStartDate = Date()
            }
            .onChange(of: entries.count) { _, _ in
                anchorOffset = 0
                dragOffset = 0
                isInteracting = false
                autoStartDate = Date()
            }
        }
        .clipped()
    }

    private func wrappedOffset(_ value: CGFloat, listHeight: CGFloat) -> CGFloat {
        guard listHeight > 0 else { return 0 }
        let remainder = value.truncatingRemainder(dividingBy: listHeight)
        return remainder >= 0 ? remainder : remainder + listHeight
    }
}
