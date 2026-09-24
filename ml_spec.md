# ML Spec: Pulse Reliability Signal

## 1. Problem statement
Daily commuters rely on the Pulse app's saved-trip feature to plan their morning and evening transits. However, frequent unpredicted transit delays cause buses to arrive long past their scheduled times, leading to broken trust and making delay-related complaints the top category of customer support tickets. This model introduces a reliability warning signal to help riders proactively identify trips that are likely to run late.

## 2. Prediction task
* **Task Type:** Binary Classification.
* **Output:** A probability score representing the likelihood that a given transit trip will experience a delay greater than 3 minutes, evaluated against a tuned decision threshold.

## 3. Features available at prediction time
The thirteen historical data columns are sorted as follows:
* **Known before the bus runs (Usable Features):** `service_date`, `route_id`, `direction_id`, `stop_id`, `time_point_id`, `time_point_order`, `point_type`, `standard_type`, `scheduled`, `scheduled_headway`, and derived features (such as hour and day of week). 
* **Identifiers (Excluded as features):** `half_trip_id`.
* **Known only after the bus runs (Excluded from features):** `actual` and `headway`.
* **Sources:** Historical files for training; live API lookups mapped by route, direction, and stop for production serving.

## 4. Label source
* **Source:** Historical MBTA arrival files.
* **Calculation:** Derived by subtracting the `scheduled` timestamp from the `actual` timestamp for every row that contains an `actual` timestamp. Rows missing `actual` or showing extreme outlier delays will be filtered or categorized during Task 2.

## 5. Metrics, baseline, and target
* **Baseline Strategy:** Majority class baseline evaluated on later weeks.
* **Primary Metric:** **Precision** over recall. 
* **Cost Trade-off:** A false "reliable" prediction (telling a rider a bus will be on time when it actually runs late) is the most expensive mistake because it burns user trust. The decision threshold will be adjusted to favor precision and minimize false negatives for delays, accepting a controlled rate of false alarms.

## 6. Non-goals
* Predicting precise delay durations down to the minute.
* Building trip routing or multi-leg navigation features.
* Utilizing live vehicle GPS positions or API-native predictions directly.
* Expanding coverage beyond bus routes into subway or commuter rail lines.

## 7. Open questions
* How to systematically handle historical rows missing `actual` timestamps without introducing selection bias.
* Whether headway-standard trips (`standard_type = Headway`) should be evaluated against standard timetable schedules.
* Establishing interactive human-in-the-loop decision gates in the training pipeline to evaluate probability distributions before locking in final production thresholds.

## 8. Change log
* Starts in Task 2.
