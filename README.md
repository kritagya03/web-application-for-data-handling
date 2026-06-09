# Web Application for Data Handling

A Web application I built for Wärtsilä after first year as an ELSYS student. The application is meant to make it easy for people with no software skills
to get their data plotted in an effective and intuitive manner. The code was uploaded to a Raspberry Pi Model 4 (Rpi4) and made to run instantly when given power, connected to Wärtsilä's Wi-Fi. 
This is so that anyone who wants to use the application can simply power the Rpi4 and go to

```sh
http://Rpi4-IP-adress:80
```

An explanation of how to use the application and how the algorithm that tracks the spikes of the data works is provided in each folder. An algorithm made to track the spikes of the data is implimented in the web application, because people often wish to analyze how the state-of-charge (SOC) is varrying in a battery when plotted, which is the purpouse of the spike taracking.
