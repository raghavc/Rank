import SwiftUI

/// Reusable DOB picker block used inside `SignupView`. Kept in the
/// `Onboarding/` folder to match the project layout in the spec.
struct DOBPicker: View {
    @Binding var dob: Date
    var minimumAge: Int = 18

    private var maxDate: Date {
        Calendar.current.date(byAdding: .year, value: -minimumAge, to: Date()) ?? Date()
    }

    private var minDate: Date {
        Calendar.current.date(byAdding: .year, value: -100, to: Date()) ?? Date()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Date of birth")
                .font(.rankCaption)
                .foregroundStyle(Color.rankMuted)

            DatePicker(
                "Date of birth",
                selection: $dob,
                in: minDate...maxDate,
                displayedComponents: [.date]
            )
            .labelsHidden()
            .datePickerStyle(.compact)
        }
    }
}
