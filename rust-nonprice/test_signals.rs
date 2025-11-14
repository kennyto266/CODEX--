// Simple test to verify signal generation compiles
use rust_nonprice::core::data::{ParameterSet, TechnicalIndicator, IndicatorType, SignalAction};
use rust_nonprice::strategy::signals;
use chrono::NaiveDate;

fn main() {
    // Create a test indicator
    let mut indicator = TechnicalIndicator::new(
        "TEST".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::ZScore,
        20,
    );
    indicator.set_value(-1.5);

    let parameters = ParameterSet::default();

    // Try to generate signals
    let result = signals::generate(&[indicator], &parameters);

    match result {
        Ok(signals) => {
            println!("Generated {} signals", signals.len());
            for signal in signals {
                println!("Signal: {:?} on {} with confidence {:.2}",
                    signal.action, signal.date, signal.confidence);
            }
        }
        Err(e) => {
            println!("Error: {:?}", e);
        }
    }
}
