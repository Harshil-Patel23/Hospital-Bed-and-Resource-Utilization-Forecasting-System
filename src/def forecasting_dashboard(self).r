        # Generate mock forecast data
        # if st.button("Generate Forecast", type="primary"):
        #     with st.spinner("Generating forecast..."):
        #         # Simulate forecast generation
        #         import time
        #         time.sleep(2)
                
        #         # Generate mock forecast
        #         last_date = self.daily_data['admission_date'].max()
        #         future_dates = pd.date_range(start=last_date + timedelta(days=1), 
        #                                    periods=forecast_days, freq='D')
                
        #         # Generate realistic forecast with seasonal patterns
        #         base_forecast = []
        #         for i, date in enumerate(future_dates):
        #             # Add weekly seasonality (lower on weekends)
        #             weekly_effect = 0.8 if date.weekday() >= 5 else 1.0
                    
        #             # Add some randomness
        #             daily_forecast = np.random.normal(
        #                 self.daily_data['admission_count'].mean() * weekly_effect, 
        #                 self.daily_data['admission_count'].std() * 0.3
        #             )
        #             base_forecast.append(max(10, int(daily_forecast)))
                
        #         forecast_df = pd.DataFrame({
        #             'date': future_dates,
        #             'forecast': base_forecast,
        #             'lower_bound': [f * 0.85 for f in base_forecast],
        #             'upper_bound': [f * 1.15 for f in base_forecast]
        #         })
                
        #         # Plot forecast
        #         fig = go.Figure()
                
        #         # Historical data
        #         recent_data = self.daily_data.tail(60)
        #         fig.add_trace(go.Scatter(
        #             x=recent_data['admission_date'],
        #             y=recent_data['admission_count'],
        #             name='Historical',
        #             line=dict(color='blue', width=2)
        #         ))
                
        #         # Forecast
        #         fig.add_trace(go.Scatter(
        #             x=forecast_df['date'],
        #             y=forecast_df['forecast'],
        #             name='Forecast',
        #             line=dict(color='red', width=2, dash='dash')
        #         ))
                
        #         # Confidence interval
        #         fig.add_trace(go.Scatter(
        #             x=forecast_df['date'].tolist() + forecast_df['date'].tolist()[::-1],
        #             y=forecast_df['upper_bound'].tolist() + forecast_df['lower_bound'].tolist()[::-1],
        #             fill='toself',
        #             fillcolor='rgba(255,0,0,0.2)',
        #             line=dict(color='rgba(255,255,255,0)'),
        #             name='Confidence Interval',
        #             showlegend=True
        #         ))
                
        #         fig.update_layout(
        #             title=f'{model_type} Forecast - Next {forecast_days} Days',
        #             xaxis_title='Date',
        #             yaxis_title='Daily Admissions',
        #             height=500
        #         )
                
        #         st.plotly_chart(fig, use_container_width=True)
                
        #         # Forecast summary
        #         st.subheader("📊 Forecast Summary")
                
        #         col1, col2, col3, col4 = st.columns(4)
                
        #         with col1:
        #             st.metric("Predicted Total", f"{sum(base_forecast):,}")
                
        #         with col2:
        #             st.metric("Daily Average", f"{np.mean(base_forecast):.1f}")
                
        #         with col3:
        #             peak_day = np.argmax(base_forecast) + 1
        #             st.metric("Peak Day", f"Day {peak_day}")
                
        #         with col4:
        #             st.metric("Peak Admissions", f"{max(base_forecast):,}")
                
        #         # Detailed forecast table
        #         st.subheader("📋 Detailed Forecast")
                
        #         # Create display dataframe
        #         display_df = forecast_df.copy()
        #         display_df['forecast'] = display_df['forecast'].round(0).astype(int)
        #         display_df['lower_bound'] = display_df['lower_bound'].round(0).astype(int)
        #         display_df['upper_bound'] = display_df['upper_bound'].round(0).astype(int)
        #         display_df['day_of_week'] = display_df['date'].dt.day_name()
                
        #         # Reorder columns for better display
        #         display_df = display_df[['date', 'day_of_week', 'forecast', 'lower_bound', 'upper_bound']]
        #         display_df.columns = ['Date', 'Day of Week', 'Forecast', 'Lower Bound', 'Upper Bound']
                
        #         st.dataframe(display_df, use_container_width=True, height=400)