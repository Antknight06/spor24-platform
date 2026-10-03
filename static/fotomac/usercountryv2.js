var checkLocalDb = function () {
    var t, e = new Date;
    try {
        return localStorage.setItem(e, e),
            t = localStorage.getItem(e) == e,
            localStorage.removeItem(e),
            t && localStorage
    } catch (t) {
        return !1
    }
}
var userCountryLibrary = {
    getCityRequestProcessStatus: false,
    writeUserCountry: function (userCountry) {
        try {
            localStorage.setItem("usercountry", JSON.stringify(userCountry));
        } catch (t) {
            return !1;
        }
    },
    addMonths: function (date, months) {
        var d = date.getDate();
        date.setMonth(date.getMonth() + +months);
        if (date.getDate() != d) {
            date.setDate(0);
        }
        return date;
    },
    addHours: function (date, hours) {
        date.setHours(date.getHours() + hours);
        return date;
    },
    checkLocalStorageData: function (isDaily, time) {

        var userCountryData = localStorage.getItem("usercountry");
        if (null != userCountryData) {
            var obj = JSON.parse(userCountryData);
            var expDate = new Date(obj.CreateDate);
            expDate = isDaily ? this.addHours(expDate, time) : expDate = this.addMonths(expDate, time);
            var today = new Date();
            if (typeof obj.CityName === 'undefined' || expDate.getTime() < today.getTime())
                this.setLocalStorageData();
        }
        else
            this.setLocalStorageData();

    },

    getLocalStorageData: function (isDaily = true, time = 1) {      
            this.checkLocalStorageData(isDaily, time);
            var userCountry = localStorage.getItem("usercountry");
            if (userCountry) {
                var userCountryParse = JSON.parse(userCountry);
                userCountryParse.CurrentDate = new Date().getTime();
            }
            return userCountryParse;        
    },
    setLocalStorageData: function () {
        if (!userCountryLibrary.getCityRequestProcessStatus) {
            userCountryLibrary.getCityRequestProcessStatus = true;
            userCountryLibrary.getCityFetchCall();
        }
    },
    getCityFetchCall: function () {
        fetch("https://ipcheck.tmgrup.com.tr/ipcheck/getcity")
           .then(response => {
                    if (!response.ok) {
                    } else {
                        return response.json();
                    }
                })
            .then(data => {
                if (data && data.Status !== undefined && data.CountryName !== undefined && data.CountryCode !== undefined && checkLocalDb()) {
                    var obj = {
                        "CountryName": data.CountryName,
                        "CountryCode": data.CountryCode,
                        "CreateDate": new Date().getTime(),
                        "Domain": location.protocol + '//' + location.hostname,
                        "Status": data.Status,
                        "CurrentDate": data.CurrentDate,
                        "Latitude": data.Latitude,
                        "Longitude": data.Longitude,
                        "IP": data.IP,
                        "SubDivisionCode": data.SubDivisionCode,
                        "CityName": data.CityName,
                        "CityNameForUrl": data.CityNameForUrl
                    };
                    userCountryLibrary.writeUserCountry(obj);
                }
            })
            .catch(error => {
                console.log(error);
            })
            .finally(() => {
                userCountryLibrary.getCityRequestProcessStatus = false;
            });
    }

};
userCountryLibrary.getLocalStorageData();