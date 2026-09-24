# ML Spec: Pulse Reliability Signal

## 1. Problem statement
Daily commuters rely on the Pulse app's saved-trip feature to plan their morning and evening transits. However, frequent unpredicted transit delays cause buses to arrive long past their scheduled times, leading to broken trust and making delay-related complaints the top category of customer support tickets. This model introduces a reliability warning signal to help riders proactively identify trips that are likely to run late.

## 2. Prediction task
* **Task Type:** Binary Classification.
* **Output:** A probability score representing the likelihood that a given transit trip will experience a delay greater than 3 minutes, evaluated against a tuned decision threshold.

## 3. Features available at prediction time
* **Usable Features (Known in advance / derived from schedule):** 
  * `service_date`, `route_id`, `direction_id`, `stop_id`, `time_point_id`
  * `time_point_order`, `point_type`, `standard_type`
  * `scheduled`, `scheduled_headway`
  * *Derived Features:* Hour of day, day of the week, route-stop interaction flags.
* **Identifiers (Excluded from features):** `half_trip_id`.
* **Data Sources:** Historical files for training pipelines; live API lookup records mapped by route, direction, and stop for production serving.

## 4. Label source
* **Source:** Historical MBTA arrival files.
* **Calculation:** Derived by subtracting the `scheduled` timestamp from the `actual` timestamp.
* **Data Cleaning Intent:** Rows lacking an `actual` timestamp (indicating cancellations or system tracking gaps) and extreme outlier delays will be measured, filtered, or explicitly categorized during Task 2 database ingestion.

## 5. Metrics, baseline, and target
* **Baseline Strategy:** Majority class baseline (predicting the most frequent class, i.e., "on-time").
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
